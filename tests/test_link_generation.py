from src.whatsapp_link_generator import WhatsAppLinkGenerator


def test_normalize_phone_accepts_country_code_digits():
    assert WhatsAppLinkGenerator.normalize_phone("+62 812-3456-789") == "628123456789"


def test_normalize_phone_rejects_too_short_numbers():
    assert WhatsAppLinkGenerator.normalize_phone("12345") == ""


def test_build_link_uses_wa_me_format():
    app = WhatsAppLinkGenerator.__new__(WhatsAppLinkGenerator)
    app.wa_format = True

    assert app.build_link("628123456789", "Hello world") == (
        "https://wa.me/628123456789?text=Hello%20world"
    )


def test_build_link_uses_api_format():
    app = WhatsAppLinkGenerator.__new__(WhatsAppLinkGenerator)
    app.wa_format = False

    assert app.build_link("628123456789", "Hello world") == (
        "https://api.whatsapp.com/send?phone=628123456789&text=Hello%20world"
    )


def test_build_link_can_use_web_whatsapp():
    app = WhatsAppLinkGenerator.__new__(WhatsAppLinkGenerator)
    app.wa_format = True

    assert app.build_link("628123456789", "Hello world", use_web=True) == (
        "https://web.whatsapp.com/send?phone=628123456789&text=Hello%20world"
    )


def test_build_link_without_message_has_no_text_parameter():
    app = WhatsAppLinkGenerator.__new__(WhatsAppLinkGenerator)
    app.wa_format = True

    assert app.build_link("628123456789") == "https://wa.me/628123456789"
