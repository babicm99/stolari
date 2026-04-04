-- Ladice LADICE_1–4: ElementSubTypeElements. Idempotent.
-- Run: python manage.py dbshell
-- Then paste this block, or: sqlite3 db.sqlite3 < scripts/insert_ladice_elementsubtypeelements.sql

BEGIN;

INSERT INTO offers_elementsubtypeelements (
  element_name,
  element_quantity,
  element_price,
  element_discount,
  element_total_price,
  formula_code,
  element_sub_type_id
)
SELECT
  v.element_name,
  1,
  0,
  0,
  0,
  v.formula_code,
  est.id
FROM offers_elementsubtype est
CROSS JOIN (
  SELECT 'Vezac/Plafon' AS element_name, 'PLAFONVEZAC_CALCULATION' AS formula_code
  UNION ALL SELECT 'Fronta', 'FRONTA_CALCULATION'
  UNION ALL SELECT 'Ledja', 'LEDJA_CALCULATION'
  UNION ALL SELECT 'Polica', 'POLICA_CALCULATION'
  UNION ALL SELECT 'Pod', 'POD_CALCULATION'
  UNION ALL SELECT 'Stranica', 'STRANICE_CALCULATION'
) AS v
WHERE est.type = 'ladice'
  AND est.code IN ('LADICE_1', 'LADICE_2', 'LADICE_3', 'LADICE_4')
  AND NOT EXISTS (
    SELECT 1
    FROM offers_elementsubtypeelements e
    WHERE e.element_sub_type_id = est.id
      AND e.element_name = v.element_name
  );

COMMIT;
