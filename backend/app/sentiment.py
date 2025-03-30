import kaggle
import tensorflow as tf

url = 'https://www.kaggle.com/models/ruhul20/twitter-sentiment-analysis'
path = kagglehub.model_download("ruhul20/twitter-sentiment-analysis/other/default")
model = tf.keras.models.load_model(path)

def analyze_sentiment(text):

    score = model.predict([text])[0]
    
    if score >= 0.6:
        return f"Positive sentiment (score: {score:.2f})"
    elif score <= 0.4:
        return f"Negative sentiment (score: {score:.2f})"
    else:
        return f"Neutral sentiment (score: {score:.2f})"

print(analyze_sentiment("I love this product!"))