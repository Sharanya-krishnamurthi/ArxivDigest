import torch
import gradio as gr
import requests
import re
from transformers import pipeline
from pdfminer.high_level import extract_text

# Load Summarization Model
summarizer = pipeline(
    "summarization", model="sshleifer/distilbart-cnn-12-6", torch_dtype=torch.bfloat16
)

def extract_arxiv_pdf_url(arxiv_url):
    """Convert arXiv abstract URL to PDF download link."""
    match = re.search(r"arxiv\.org\/abs\/(\d+\.\d+)", arxiv_url)
    if match:
        return f"https://arxiv.org/pdf/{match.group(1)}.pdf"
    return None


def download_and_extract_text(arxiv_url):
    """Download arXiv PDF and extract text using pdfminer."""
    pdf_url = extract_arxiv_pdf_url(arxiv_url)
    if not pdf_url:
        return "Invalid arXiv URL."

    response = requests.get(pdf_url)
    if response.status_code != 200:
        return "Failed to download the PDF."

    # Save PDF temporarily
    pdf_path = "paper.pdf"
    with open(pdf_path, "wb") as f:
        f.write(response.content)

    # Extract text from PDF using pdfminer
    try:
        text = extract_text(pdf_path)
        return text[:10000]  # Limit input length for summarization
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def chunk_text(text, chunk_size=1000):
    """Break the text into smaller chunks to fit the model's token limit."""
    text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    return text_chunks


def generate_summary(arxiv_url):
    """Summarize research paper from arXiv link."""
    text = download_and_extract_text(arxiv_url)
    if "Failed" in text or "Invalid" in text:
        return text

    # Chunk the text into smaller parts if needed
    chunks = chunk_text(text)

    # Summarize each chunk and combine results
    summaries = []
    # for chunk in chunks[:5]:
    #     summary = summarizer(chunk)
    #     summaries.append(summary[0]["summary_text"])
    summary = summarizer(text[:1000])
    summaries.append(summary[0]["summary_text"])

    # Combine the individual summaries into one
    final_summary = " ".join(summaries)
    return final_summary


# Gradio App
gr.close_all()
demo = gr.Interface(
    fn=generate_summary,
    inputs=[gr.Text(label="ArXiv Paper URL")],
    outputs=[gr.Textbox(label="Paper Summary")],
    title="Research Paper Summarizer",
    description="Enter an arXiv link to get a concise summary of the research paper.",
)

demo.launch()
