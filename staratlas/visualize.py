import os

import plotly.express as px
import pycountry


def _alpha2_to_alpha3(alpha2):
    try:
        country = pycountry.countries.get(alpha_2=alpha2)
        if country:
            return country.alpha_3
    except LookupError:
        return None
    return None


def render_world_map(country_counts, output_png, output_html=None):
    if not country_counts:
        return False
    locations = []
    values = []
    for alpha2, count in country_counts.items():
        alpha3 = _alpha2_to_alpha3(alpha2)
        if not alpha3:
            continue
        locations.append(alpha3)
        values.append(count)
    if not locations:
        return False

    fig = px.choropleth(
        locations=locations,
        locationmode="ISO-3",
        color=values,
        color_continuous_scale="Blues",
        title="Stargazers by Country",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))

    os.makedirs(os.path.dirname(output_png), exist_ok=True)
    fig.write_image(output_png, format="png", width=1200, height=600, scale=2)
    if output_html:
        fig.write_html(output_html, include_plotlyjs="cdn")
    return True
