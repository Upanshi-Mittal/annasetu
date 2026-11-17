import io

import qrcode
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas

from certificates.models import Certificate
from donations.models import Donation


def generate_pdf_certificate(certificate):
    """Generate a clean, CSR-ready PDF certificate using ReportLab."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)

    # Background frame
    p.setStrokeColor(colors.HexColor('#16A34A'))
    p.setLineWidth(4)
    p.rect(20, 20, width - 40, height - 40)
    p.setStrokeColor(colors.HexColor('#F59E0B'))
    p.setLineWidth(1.5)
    p.rect(26, 26, width - 52, height - 52)

    # Title
    p.setFont("Helvetica-Bold", 32)
    p.setFillColor(colors.HexColor('#14532D'))
    p.drawCentredString(width / 2.0, height - 90, "AnnaSetu Food Rescue Certificate")

    # Subtitle
    p.setFont("Helvetica", 14)
    p.setFillColor(colors.HexColor('#4B5563'))
    p.drawCentredString(width / 2.0, height - 120, "Official Certificate of Appreciation for Food Redistribution & CSR Impact")

    # Recipient
    p.setFont("Helvetica", 16)
    p.drawString(100, height - 180, "Presented to:")
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor('#16A34A'))
    p.drawString(100, height - 215, str(certificate.donor.display_name))

    # Impact stats
    p.setFont("Helvetica", 14)
    p.setFillColor(colors.HexColor('#1F2937'))
    p.drawString(100, height - 260, f"Meals Rescued: {certificate.total_servings} servings")
    p.drawString(100, height - 285, f"Food Diverted from Waste: {certificate.total_kg:.1f} kg")
    p.drawString(100, height - 310, f"Estimated CO2 Emissions Prevented: {certificate.co2_avoided_kg:.1f} kg CO2e")

    # Serial and verification URL
    verify_url = f"{settings.SITE_URL}/verify/{certificate.serial_number}/"
    p.setFont("Helvetica", 11)
    p.setFillColor(colors.HexColor('#6B7280'))
    p.drawString(100, height - 360, f"Serial Number: {certificate.serial_number}")
    p.drawString(100, height - 380, f"Verification URL: {verify_url}")

    # Generate QR Code image in PDF
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    from reportlab.lib.utils import ImageReader
    p.drawImage(ImageReader(qr_buffer), width - 220, height - 320, width=120, height=120)
    p.setFont("Helvetica", 9)
    p.drawCentredString(width - 160, height - 335, "Scan to Verify Authenticity")

    # Signatures
    p.setStrokeColor(colors.HexColor('#9CA3AF'))
    p.setLineWidth(1)
    p.line(100, 70, 280, 70)
    p.drawString(100, 55, "Authorized Signatory, AnnaSetu")

    p.line(width - 320, 70, width - 140, 70)
    p.drawString(width - 320, 55, f"Date: {certificate.created_at.strftime('%B %d, %Y')}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


@login_required
def certificate_download_view(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk, donor=request.user)
    pdf_buffer = generate_pdf_certificate(certificate)
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="annasetu-certificate-{certificate.serial_number}.pdf"'
    return response


@login_required
def certificate_generate_donation_view(request, donation_id):
    donation = get_object_or_404(Donation, pk=donation_id, donor=request.user, status='delivered')
    cert, created = Certificate.objects.get_or_create(
        donor=request.user,
        donation=donation,
        defaults={
            'cert_type': 'per_donation',
            'total_servings': donation.quantity_servings,
            'total_kg': donation.kg_estimate,
            'co2_avoided_kg': donation.co2_avoided,
        }
    )
    return redirect('certificate_download', pk=cert.pk)


def certificate_verify_view(request, serial):
    """Public certificate verification page."""
    try:
        certificate = Certificate.objects.select_related('donor', 'donation').get(serial_number=serial)
        is_valid = True
    except Certificate.DoesNotExist:
        certificate = None
        is_valid = False

    return render(request, 'certificates/verify.html', {
        'certificate': certificate,
        'serial': serial,
        'is_valid': is_valid,
    })
