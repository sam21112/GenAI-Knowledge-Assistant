from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

processor, model = None, None

def get_blip():
    global processor, model
    if processor is None or model is None:
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

def caption_image(image_path):
    proc, mdl = get_blip()
    img = Image.open(image_path).convert("RGB")
    inputs = proc(img, return_tensors="pt")
    out = mdl.generate(**inputs)
    return proc.decode(out[0], skip_special_tokens=True)

def extract_caption(image_path):
    raw_image = Image.open(image_path).convert('RGB')
    inputs = processor(raw_image, return_tensors="pt")
    out = model.generate(**inputs)
    return processor.decode(out[0], skip_special_tokens=True)
