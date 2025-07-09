

import re
import string
import spacy
import tensorflow as tf
from transformers import BertTokenizer, TFBertForSequenceClassification

# Initialize spaCy and tokenizer/model ONCE (global scope for efficiency)
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
tokenizer = BertTokenizer.from_pretrained("model_trained_colab")
model = TFBertForSequenceClassification.from_pretrained("model_trained_colab")

SENTIMENT_WHITELIST = {
    # Intensifiers
    "absolutely", "barely", "completely", "entirely", "exceptionally", "extremely",
    "fully", "highly", "incredibly", "insanely", "marginally", "moderately",
    "particularly", "partially", "quite", "really", "remarkably", "slightly",
    "somewhat", "terribly", "thoroughly", "totally", "too", "utterly", "very",
    # Negations (standard + variants without apostrophes)
    "ain't", "aint", "aren't", "arent", "can't", "cant", "cannot", "couldn't", "couldnt",
    "didn't", "didnt", "doesn't", "doesnt", "don't", "dont", "hadn't", "hadnt",
    "hasn't", "hasnt", "haven't", "havent", "isn't", "isnt", "mightn't", "mightnt",
    "mustn't", "mustnt", "neither", "never", "no", "nobody", "none", "nor", "not",
    "nothing", "nowhere", "shouldn't", "shouldnt", "wasn't", "wasnt", "weren't",
    "werent", "wouldn't", "wouldnt", "wont", "won't",

    # Contrast/Concession
    "although", "but", "despite", "except", "however", "though", "yet"
}


def clean_text(txt):
    """Clean text by removing URLs, punctuation, numbers, and extra spaces"""
    txt = txt.lower().strip()
    txt = re.sub(r"http\S+|www\S+|https\S+", '', txt, flags=re.MULTILINE)
    txt = re.sub(f"[{re.escape(string.punctuation)}]", '', txt)
    txt = re.sub(r'\d+', '', txt)
    return re.sub(r'\s+', ' ', txt)


def lemmatize_and_filter(text):
    """Process text with spaCy and retain meaningful words"""
    doc = nlp(text)
    tokens = []
    for token in doc:
        if token.lemma_.lower() in SENTIMENT_WHITELIST:
            tokens.append(token.lemma_)
        elif token.is_alpha and not token.is_stop:
            tokens.append(token.lemma_)
    return " ".join(tokens)


def predict_sentiment(text):
    """End-to-end sentiment prediction pipeline"""
    # Clean and preprocess
    cleaned = clean_text(text)
    processed = lemmatize_and_filter(cleaned)

    # Tokenize and predict
    inputs = tokenizer(
        processed,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors='tf'
    )

    # Model inference
    outputs = model(inputs)
    probabilities = tf.nn.softmax(outputs.logits, axis=-1).numpy()[0]

    # Interpret results
    sentiment_labels = {0: "negative", 1: "neutral", 2: "positive"}
    predicted_class = probabilities.argmax()
    sentiment = sentiment_labels.get(predicted_class, "unknown")
    confidence = float(probabilities.max())

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "probabilities": {
            "negative": float(probabilities[0]),
            "neutral": float(probabilities[1]),
            "positive": float(probabilities[2])
        },
        "lemmatize": processed
    }


#
# if __name__ == "__main__":
#     sample_text = "clear explanation, well defined theory"
#     result = predict_sentiment(sample_text)
#     print(f"Sentiment: {result['sentiment']} (Confidence: {result['confidence']:.2f})")
#     print(f"Probabilities: {result['probabilities']}")
#     print(f"Lemma: {result['lemmatize']}")

