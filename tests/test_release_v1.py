from streamlit.testing.v1 import AppTest

CODES = ('tokyo osaka kanagawa fukuoka chiba saitama sapporo sendai niigata '
         'hiroshima takamatsu kanazawa shizuoka kyoto kobe nagano okayama kumamoto '
         'naha matsuyama morioka').split()


def test_release_all_21_presets_render_with_year_and_address_limitations():
    app = AppTest.from_file('app.py').run()
    assert len(app.selectbox[1].options) == 21
    for code in CODES:
        app.selectbox[1].set_value(code).run()
        assert not app.exception
        captions = '\n'.join(c.value for c in app.caption)
        assert '確認済みの21地域' in captions
        assert '全国すべての自治体には対応していません' in captions
        assert '2026年1月1日' in captions
        assert '2026-04' in captions
        assert '12か月' in captions
        assert len(app.table[0].value) >= 12


def test_release_english_scope_is_equally_explicit():
    app = AppTest.from_file('app.py').run()
    app.selectbox[0].set_value('en').run()
    assert not app.exception
    captions = '\n'.join(c.value for c in app.caption)
    assert '21 verified regional presets' in captions
    assert 'Unverified candidates are not selectable' in captions
    assert 'January 1, 2026' in captions
