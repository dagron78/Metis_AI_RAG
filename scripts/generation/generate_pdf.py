from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import os

def generate_test_pdf(output_path="sample_report.pdf"):
    """Generate a sample PDF report for testing Metis RAG"""
    
    # Create the PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = styles["Heading1"]
    title_style.alignment = 1  # Center alignment
    
    heading2_style = styles["Heading2"]
    heading3_style = styles["Heading3"]
    
    normal_style = styles["Normal"]
    normal_style.spaceAfter = 12
    
    # Create the content elements
    elements = []
    
    # Title
    elements.append(Paragraph("Quarterly Business Report", title_style))
    elements.append(Spacer(1, 24))
    
    # Executive Summary
    elements.append(Paragraph("Executive Summary", heading2_style))
    elements.append(Paragraph(
        """This quarterly report provides an overview of business performance for Q1 2025. 
        Overall, the company has seen strong growth in key metrics including revenue, customer 
        acquisition, and product engagement. This document summarizes the performance across 
        departments and outlines strategic initiatives for the upcoming quarter.""",
        normal_style
    ))
    elements.append(Spacer(1, 12))
    
    # Financial Performance
    elements.append(Paragraph("Financial Performance", heading2_style))
    elements.append(Paragraph(
        """The company achieved $4.2M in revenue for Q1, representing a 15% increase year-over-year. 
        Gross margin improved to 72%, up from 68% in the previous quarter. Operating expenses were 
        kept under control at $2.8M, resulting in a net profit of $1.4M.""",
        normal_style
    ))
    
    # Create a table for financial data
    financial_data = [
        ['Metric', 'Q1 2025', 'Q4 2024', 'Q1 2024', 'YoY Change'],
        ['Revenue', '$4.2M', '$3.8M', '$3.65M', '+15%'],
        ['Gross Margin', '72%', '68%', '65%', '+7%'],
        ['Operating Expenses', '$2.8M', '$2.7M', '$2.5M', '+12%'],
        ['Net Profit', '$1.4M', '$1.1M', '$0.9M', '+56%'],
    ]
    
    table = Table(financial_data, colWidths=[120, 80, 80, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 24))
    
    # Product Development
    elements.append(Paragraph("Product Development", heading2_style))
    elements.append(Paragraph(
        """The product team successfully launched 3 major features this quarter:""",
        normal_style
    ))
    
    # Feature list
    features = [
        "Advanced Analytics Dashboard: Providing deeper insights into user behavior",
        "Mobile Application Redesign: Improving user experience and engagement",
        "API Integration Platform: Enabling third-party developers to build on our platform"
    ]
    
    for feature in features:
        elements.append(Paragraph(f"• {feature}", normal_style))
    
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        """User engagement metrics show a 22% increase in daily active users following these releases. 
        The product roadmap for Q2 focuses on scalability improvements and enterprise features.""",
        normal_style
    ))
    elements.append(Spacer(1, 12))
    
    # Marketing and Sales
    elements.append(Paragraph("Marketing and Sales", heading2_style))
    elements.append(Paragraph(
        """The marketing team executed campaigns that generated 2,500 new leads, a 30% increase from 
        the previous quarter. Sales conversion rate improved to 12%, resulting in 300 new customers. 
        Customer acquisition cost (CAC) decreased by 15% to $350 per customer.""",
        normal_style
    ))
    
    # Customer Success
    elements.append(Paragraph("Customer Success", heading2_style))
    elements.append(Paragraph(
        """Customer retention rate remained strong at 94%. Net Promoter Score (NPS) improved from 
        42 to 48. The support team handled 3,200 tickets with an average response time of 2.5 hours 
        and a satisfaction rating of 4.8/5.""",
        normal_style
    ))
    
    # Strategic Initiatives for Q2
    elements.append(Paragraph("Strategic Initiatives for Q2", heading2_style))
    elements.append(Paragraph("The following initiatives are planned for Q2 2025:", normal_style))
    
    initiatives = [
        "International Expansion: Launch in European markets",
        "Enterprise Solution: Develop and release enterprise-grade features",
        "Strategic Partnerships: Form alliances with complementary service providers",
        "Operational Efficiency: Implement automation to reduce operational costs"
    ]
    
    for initiative in initiatives:
        elements.append(Paragraph(f"• {initiative}", normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    print(f"PDF generated successfully at {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)

if __name__ == "__main__":
    generate_test_pdf()