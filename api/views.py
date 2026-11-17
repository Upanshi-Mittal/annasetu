from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from api.serializers import (
    ClaimSerializer,
    DeliveryTaskSerializer,
    DonationSerializer,
    NotificationSerializer,
    UserSerializer,
)
from donations.models import Donation
from logistics.models import Claim, DeliveryTask
from logistics.services import accept_task, confirm_delivery, confirm_pickup, create_claim, verify_qr_scan
from notifications.models import Notification


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DonationViewSet(viewsets.ModelViewSet):
    queryset = Donation.objects.all().select_related('donor')
    serializer_class = DonationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['food_type', 'is_cooked', 'status']
    search_fields = ['title', 'description', 'pickup_address']
    ordering_fields = ['created_at', 'safe_until', 'quantity_servings']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(donor=self.request.user)


class ClaimViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_ngo:
            return Claim.objects.filter(ngo=user)
        elif user.is_donor:
            return Claim.objects.filter(donation__donor=user)
        return Claim.objects.all()

    def perform_create(self, serializer):
        donation = serializer.validated_data['donation']
        servings = serializer.validated_data['servings_requested']
        note = serializer.validated_data.get('note', '')
        claim, _ = create_claim(donation, self.request.user, servings, note)
        serializer.instance = claim


class DeliveryTaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DeliveryTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_volunteer:
            return DeliveryTask.objects.filter(volunteer=user)
        elif user.is_ngo:
            return DeliveryTask.objects.filter(claim__ngo=user)
        elif user.is_donor:
            return DeliveryTask.objects.filter(donation__donor=user)
        return DeliveryTask.objects.all()

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        task = self.get_object()
        if not request.user.is_volunteer:
            return Response({'error': 'Only volunteers can accept tasks.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            task = accept_task(task, request.user)
            return Response(self.get_serializer(task).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'marked all read'})


class QRScanViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def scan(self, request):
        token = request.data.get('token')
        scan_type = request.data.get('type')  # 'pickup' or 'delivery'
        task_id = request.data.get('task_id')

        if not token or not scan_type or not task_id:
            return Response({'error': 'token, type, and task_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = DeliveryTask.objects.get(pk=task_id)
        except DeliveryTask.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

        token_data = verify_qr_scan(token)
        if not token_data:
            return Response({'error': 'Invalid or expired QR code'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if scan_type == 'pickup':
                task = confirm_pickup(task, request.user)
            elif scan_type == 'delivery':
                task = confirm_delivery(task, request.user)
            else:
                return Response({'error': 'Invalid scan type'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'status': 'success', 'task': DeliveryTaskSerializer(task).data})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
