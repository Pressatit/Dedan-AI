# nlp_model.py
import tensorflow as tf
from tensorflow import keras

class DEKAINLP:
    def __init__(self, model_path="models/dekai_nlp"):
        print("🔹 Loading DEKAI-NLP model...")
        self.model = keras.models.load_model(model_path)
        print("✅ NLP model ready.")

        vocab_path = "/kaggle/input/dekai-vocab-dataset/dekai_vocab.txt"
        with open(vocab_path, "r") as f:
         vocab = f.read().splitlines()
        
        def standardize_keep_tokens(text):
            lower = tf.strings.lower(text)
            cleaned = tf.strings.regex_replace(lower, r"[^a-z0-9<> ]", "")
            cleaned = tf.strings.regex_replace(cleaned, r"\s+", " ")
            return cleaned

        vectorizer = tf.keras.layers.TextVectorization(
            max_tokens=40000,
            output_mode="int",
            output_sequence_length=40,
            standardize=standardize_keep_tokens
)
        vectorizer.set_vocabulary(vocab)     
    
        with open("models/vocab.txt", "r") as f:
            self.vocab = [line.strip() for line in f]
        self.word2idx = {w: i for i, w in enumerate(self.vocab)}
        self.idx2word = {i: w for w, i in self.word2idx.items()}

    def encode(self, text):
        tokens = [self.word2idx.get(w, 1) for w in text.lower().split()]  # 1=UNK
        return tf.expand_dims(tokens, axis=0)

    def decode(self, token_ids):
        return " ".join(self.idx2word.get(int(i), "<unk>") for i in token_ids if int(i) != 0)

    def beam_search(self, input_seq, beam_width=3, max_len=30):
    # Start with <start> token
     sequences = [[list(input_seq[0].numpy()), 0.0]]  # [tokens, score]

     for _ in range(max_len):
      all_candidates = []
      for seq, score in sequences:
             inp = tf.expand_dims(seq, axis=0)
             preds = self.model(inp, training=False)
             probs = tf.nn.softmax(preds[0, -1])  # last token probabilities

             top_k = tf.math.top_k(probs, k=beam_width)
             for i in range(beam_width):
                token_id = int(top_k.indices[i])
                candidate = [seq + [token_id], score - tf.math.log(top_k.values[i])]
                all_candidates.append(candidate)

        # sort all candidates by score
      ordered = sorted(all_candidates, key=lambda tup: tup[1])
      sequences = ordered[:beam_width]

     return sequences[0][0]  # best token sequence


    def chat(self, prompt):
      inp = self.encode(prompt)
      best_tokens = self.beam_search(inp, beam_width=5)
      return self.decode(best_tokens)


