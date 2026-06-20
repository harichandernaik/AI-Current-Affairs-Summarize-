import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from nlp_service import analyze, classify, summarize
from pdf_ingestion import split_articles_from_text

class NLPTests(unittest.TestCase):
    def test_classification(self): self.assertEqual(classify("climate forest biodiversity emission"), "Environment")
    def test_classification_resists_generic_technology_noise(self):
        polity = "Digital Competition Bill strengthens parliament oversight, constitutional rights and market regulation by the ministry."
        economy = "RBI monetary policy, inflation and bank lending changed market expectations despite digital reporting tools."
        social = "Health education nutrition and gender welfare delivery improved through a digital dashboard."
        self.assertEqual(classify(polity), "Polity")
        self.assertEqual(classify(economy), "Economy")
        self.assertEqual(classify(social), "Social Issues")
    def test_summary_is_shorter(self):
        text = "One important sentence about the economy. Inflation affects household budgets significantly. Banks changed lending rates this week. Markets responded to the policy announcement."
        self.assertLessEqual(len(summarize(text).split(".")), 4)
    def test_analysis_shape(self):
        result = analyze("Quantum satellite", "A quantum technology satellite supports secure communication and research. Scientists tested the digital system successfully.")
        self.assertTrue(result["keywords"]); self.assertTrue(result["mcqs"])
    def test_newspaper_article_splitting(self):
        text = "PARLIAMENT REVIEWS NEW DIGITAL COMPETITION BILL\n" + ("The parliament and ministry reviewed constitutional safeguards for digital markets and consumer rights. " * 7) + "\n\nINDIA EXPANDS GREEN HYDROGEN PROGRAMME\n" + ("The climate and renewable energy programme will reduce emissions and support conservation. " * 7)
        articles = split_articles_from_text(text)
        self.assertEqual(len(articles), 2)

if __name__ == "__main__": unittest.main()
