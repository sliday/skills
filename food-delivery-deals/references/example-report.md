# Example report

A real run on 2026-10-20 at about 19:05 CEST, Warsaw Centrum (52.230, 21.012). Use it for the shape of a report. The deals themselves are gone by now.

What the agent ran:
```
python3 scripts/wolt.py deals --lat 52.2297 --lon 21.0122 --venues 3
python3 scripts/wolt.py items hawaiian-poke-bowl-centrum --sort price --currency PLN
POST https://www.ubereats.com/api/getSearchSuggestionsV1  {"userQuery":"hawaiian poke bowl"}
```

---

**Best usable deal: Hawaiian Poke Bowl - Centrum on Wolt, 30% off up to 15 PLN.**
Salmon bowl 49.00 + Vegetarian bowl 45.00 = 94.00 PLN. 30% would be 28.20 PLN, but the cap stops it at 15.00, so the food costs **79.00 PLN**. The venue also runs its own 0 PLN delivery offer for home delivery. Without it, delivery is 1.25 PLN plus up to 13.30 PLN by distance. Minimum order: 30 PLN.

| Option | Offer | Order | Food total | Notes |
|---|---|---|---|---|
| Hawaiian Poke Bowl - Centrum (Wolt, 9.8) | 30% off, max 15 PLN | 2 bowls | 79.00 PLN | own free delivery |
| Nori Sushi Żoliborz (Wolt) | 15% off sets | Set 1, 26 pcs | 84.15 PLN (was 99.00) | min order 80 PLN, delivery from 6.00 PLN |
| Zapiekanki Wisła (Wolt, 9.8) | 10 PLN off from 75 PLN | not priced | | also "Buy 2, pay for 1" on 2 items until 23 Oct |

**Assumed:** two bowls for two people; not a new Wolt user; no Wolt+. The city-wide new-user offers ("15 PLN off over 35 PLN", "0 PLN delivery fee") are left out.

**Not checked:**
- The service fee. Wolt shows it only at checkout.
- Whether the 30% and the free delivery combine. Check the cart in the app before you pay.
- Other apps. An Uber Eats search for "hawaiian poke bowl" found only other chains (Poke Bowl Marszałkowska, Poke Bowl Chmielna), so there is no like-for-like price.

Checked 2026-10-20 at about 19:05 CEST. Offers change during the day.

---

Why this shape works:
- It leads with one deal and the money the user pays, with the cap applied, not the badge.
- It names the fees it could not see and the assumptions that change the answer.
- It reports a failed cross-app match instead of comparing different restaurants.
