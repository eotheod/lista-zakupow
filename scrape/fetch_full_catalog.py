import requests
from supabase import create_client, Client

SUPABASE_URL = "https://skkthhfvkwyrzjhkdwtc.supabase.co"
SUPABASE_KEY = "sb_publishable_bKzTnL_EzNJTweOwfSDG7A_UTlYBqka"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Gwarantowana baza drogeryjna i kosmetyczna (Rossmann / Dyskonty)
GUARANTEED_DROGERIA = [
    "Dove Mydło w kostce 90g", "Dove Żel pod prysznic 500ml", "Dove Antiperspirant Spray 150ml",
    "Nivea Krem 150ml", "Nivea Żel pod prysznic 500ml", "Nivea Szampon do włosów 400ml",
    "Garnier Płyn Micelarny 400ml", "Garnier Szampon Fructis 400ml",
    "Colgate Pasta do zębów Total 75ml", "Colgate Szczoteczka do zębów Medium",
    "Gillette Pianka do golenia 200ml", "Gillette Maszynki do golenia 3 szt.",
    "Isana Żel pod prysznic 300ml", "Isana Mydło w płynie zapas 500ml",
    "Ariel Kapsułki do prania 30 szt.", "Persil Żel do prania 1.5L",
    "Velvet Papier toaletowy 8 rolek", "Velvet Ręcznik papierowy 2 rolki"
]

# 2. Szerokie frazeologiczne kategorie produktów
SEARCH_CATEGORIES = [
    "płatki", "platki", "owsianka", "musli", "mąka", "cukier", "makaron", "ryż", "kasza", "dżem", "miód", "nutella",
    "chleb", "bułka", "masło", "margaryna", "mleko", "ser", "twaróg", "jogurt", "skyr", "kefir", "śmietana", "serek",
    "chipsy", "snacki", "paluszki", "orzechy", "popcorn", "czekolada", "baton", "ciastka", "wafle", "cukierki", "żelki",
    "szynka", "parówki", "kiełbasa", "kabanosy", "kurczak", "schab", "mielone", "łosoś", "tuńczyk",
    "woda", "sok", "napój", "cola", "pepsi", "sprite", "energetyk", "monster", "red bull", "kawa", "herbata", "piwo",
    "ketchup", "majonez", "musztarda", "olej", "oliwa", "pomidory", "ogórki", "konserwa",
    "szampon", "mydło", "żel", "pasta", "papier", "ręcznik", "proszek", "płyn", "kapsułki", "pampers", "pasta do zębów"
]

SHOPS = ["lidl", "biedronka", "rossmann", "zabka"]

def fetch_master_catalog():
    print("🚀 Generowanie PEŁNEJ bazy produktów dla wszystkich sklepów (w tym kosmetyki i drogeria)...")
    all_products = []
    seen_keys = set()
    headers = {"User-Agent": "SmartZakupyApp/9.0 (Ultimate Full Catalog)"}

    # A. Wgrywanie gwarantowanej bazy drogeryjnej (Dove, Nivea, Colgate itp.)
    for item in GUARANTEED_DROGERIA:
        for shop in SHOPS:
            dedup_key = f"{shop}_{item.lower()}"
            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                all_products.append({
                    "shop_id": shop,
                    "title": item,
                    "price_promo": round(4.99 + (len(item) % 12) * 0.8, 2),
                    "price_regular": round(6.99 + (len(item) % 12) * 1.1, 2),
                    "category": "Kosmetyki",
                    "is_promo": True
                })

    # B. Pobieranie z API Open Food Facts dla pozostałych ponad 60 kategorii
    for term in SEARCH_CATEGORIES:
        url = f"https://pl.openfoodfacts.org/cgi/search.pl?search_terms={term}&search_tag=knowledge_panel&json=1&page_size=40"
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                products = res.json().get("products", [])
                for p in products:
                    name = p.get("product_name_pl") or p.get("product_name")
                    if name and len(name.strip()) > 2:
                        raw_name = name.strip()[:70]
                        title = raw_name if term.lower() in raw_name.lower() else f"{term.capitalize()} {raw_name}"
                        clean_title = title[:80]
                        
                        for shop in SHOPS:
                            dedup_key = f"{shop}_{clean_title.lower()}"
                            if dedup_key not in seen_keys:
                                seen_keys.add(dedup_key)
                                all_products.append({
                                    "shop_id": shop,
                                    "title": clean_title,
                                    "price_promo": round(2.49 + (len(clean_title) % 15) * 0.55, 2),
                                    "price_regular": round(3.99 + (len(clean_title) % 15) * 0.75, 2),
                                    "category": term.capitalize(),
                                    "is_promo": (len(clean_title) % 2 == 0)
                                })
        except Exception as e:
            print(f"⚠️ Pominięto '{term}': {e}")

    return all_products

def main():
    catalog = fetch_master_catalog()
    
    if catalog:
        print(f"\n⚡ Łącznie wygenerowano {len(catalog)} produktów!")
        print("🧹 Czyszczenie bazy w Supabase...")
        try:
            supabase.table("products").delete().neq("title", "").execute()
        except Exception as e:
            print(f"Info czyszczenie: {e}")
        
        print("💾 Zapisywanie danych w Supabase (paczki po 100)...")
        chunk_size = 100
        for i in range(0, len(catalog), chunk_size):
            chunk = catalog[i:i + chunk_size]
            supabase.table("products").insert(chunk).execute()
            print(f" Zapisano {min(i + chunk_size, len(catalog))} / {len(catalog)}...")

        print(f"\n✅ SUKCES! Baza zawiera teraz {len(catalog)} produktów (w tym pełne marki kosmetyczne dla Rossmanna)!")

if __name__ == "__main__":
    main()