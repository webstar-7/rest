# rest

NYANSATEK Restaurant, served at **nyansatek.rest**: the restaurant edition of NYANSATEK POS
(nyansatek.shop). Orders for eat in, takeaway and delivery, a kitchen screen, a menu with a
sold-out switch per dish, and online orders through nyansatek.food.

- It uses the same database as Shop and Store. A restaurant is an `organizations` row with
  `vertical = 'food'`. The database changes are in `webstar-7/nyansatek-pos`, under
  `supabase/migrations/20261115020000_restaurants.sql`.
- `index.html` is generated from Shop's `index.html` by `tools/build_from_shop.py`; the
  restaurant-only code is in `tools/rest-layer.js` and `tools/rest-layer.css`. Change those and
  re-run the script rather than editing `index.html` by hand, or the next rebuild loses the edit.
- `menu/` is each restaurant's own online menu page (`nyansatek.rest/menu/?s=<name>`).
