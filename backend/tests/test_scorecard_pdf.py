import json
from datetime import date
from io import BytesIO

import pytest
from pypdf import PdfReader

from app.models import Game
from app.pdf.scorecard import build_scorecard_field_values, render_scorecard_pdf


@pytest.mark.parametrize('ratings', [
    {'BT': 0, 'OBT': 0}, {'bt': 0, 'obt': 0},
    {'AVG': 0.0, 'OBP': 0.0}, {'avg': 0.0, 'obp': 0.0},
])
def test_populated_pdf_preserves_zero_ratings_and_appearances(ratings):
    game = Game(game_id='test', game_date=date(2026, 9, 2),
                away_team='Padres', home_team='Reds', description='Regular Season')
    players = [
        {'Team': 'Padres', 'Type': 'Hitter', 'Name': 'Fernando Tatis Jr.',
         'BatOrder': 1, 'Pos': 'RF', 'Hand': 'R', 'Traits': 'P-- C- S- D+', **ratings},
        {'Team': 'Reds', 'Type': 'Hitter', 'Name': 'Elly De La Cruz',
         'BatOrder': 1, 'Pos': 'SS', 'Hand': 'S', 'BT': 27, 'OBT': 35},
    ]
    values = build_scorecard_field_values(game, json.dumps({'players': players}))
    pdf = render_scorecard_pdf(values)
    assert pdf.startswith(b'%PDF-')
    reader = PdfReader(BytesIO(pdf))
    assert len(reader.pages) == 2
    fields = reader.get_fields()
    for page_values in values.values():
        for key, expected in page_values.items():
            if key in fields and fields[key].get('/FT') == '/Tx':
                assert fields[key].get('/V') == expected
    assert fields['AWAYBT.0']['/V'] == '0'
    assert fields['AWAYOBT.0']['/V'] == '0'
    assert fields['HOMENAME.0']['/V'] == 'Elly De La Cruz'
    assert not reader.trailer['/Root']['/AcroForm']['/NeedAppearances'].value
    populated_widgets = 0
    for page in reader.pages:
        for ref in page['/Annots']:
            widget = ref.get_object()
            field, name_parts = widget, []
            while field is not None:
                if field.get('/T'):
                    name_parts.insert(0, str(field['/T']))
                parent = field.get('/Parent')
                field = parent.get_object() if parent else None
            name = '.'.join(name_parts)
            expected = fields.get(name, {}).get('/V')
            if expected:
                actual = widget.get('/V')
                if actual is None and widget.get('/Parent'):
                    actual = widget['/Parent'].get('/V')
                assert actual == expected
                assert widget['/AP']['/N'].get_data()
                populated_widgets += 1
    assert populated_widgets > 10
