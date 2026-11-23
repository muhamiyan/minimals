from app.infra.seo import STATIC_PUBLIC_PAGES, save_brand
from framework.extensions import db


def test_static_public_pages_are_indexable_and_in_sitemap(app, client):
    with app.app_context():
        save_brand(
            db.session,
            {"name": "Yayasan Islam Selaparang", "siteUrl": "https://selaparang.test"},
        )
        db.session.commit()

    sitemap = client.get("/sitemap.xml").get_data(as_text=True)

    for path in STATIC_PUBLIC_PAGES:
        head = client.get(path).get_data(as_text=True)
        assert 'name="robots" content="index, follow"' in head
        assert f'rel="canonical" href="https://selaparang.test{path}"' in head
        assert f"<loc>https://selaparang.test{path}</loc>" in sitemap
