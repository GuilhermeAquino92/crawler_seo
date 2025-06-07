from crawler import crawl
import pandas as pd

dominio = "https://www.alastin.com"
resultado = crawl(dominio)

df = pd.DataFrame(resultado)
df.to_excel("resultado_crawler.xlsx", index=False)
print("✅ Crawl finalizado. Resultados salvos em Excel.")
