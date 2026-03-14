import os

import plotly.express as px
import pycountry


THEMES = {
    "light": {
        "bg": "#ffffff",
        "font": "#24292f",
        "primary": "#0969da",
        "map_scale": "Blues",
        "template": "plotly_white",
        "land": "#f6f8fa",
    },
    "dark": {
        "bg": "#0d1117",
        "font": "#c9d1d9",
        "primary": "#58a6ff",
        "map_scale": "Blues",
        "template": "plotly_dark",
        "land": "#0d1117",
    },
}


def _alpha2_to_alpha3(alpha2):
    try:
        country = pycountry.countries.get(alpha_2=alpha2)
        if country:
            return country.alpha_3
    except LookupError:
        return None
    return None


def _apply_theme(fig, theme_name):
    theme = THEMES.get(theme_name, THEMES["light"])
    fig.update_layout(
        template=theme["template"],
        paper_bgcolor=theme["bg"],
        plot_bgcolor=theme["bg"],
        font=dict(color=theme["font"], family="-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"),
        margin=dict(l=20, r=20, t=60, b=20),
        title_font=dict(size=20, family="inherit"),
    )
    return theme


def render_world_map(country_counts, output_png, output_html=None, theme="light"):
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
        color_continuous_scale=THEMES.get(theme, THEMES["light"])["map_scale"],
        title="Stargazers by Country",
    )
    applied = _apply_theme(fig, theme)
    fig.update_geos(
        showframe=False,
        showcoastlines=False,
        projection_type="equirectangular",
        bgcolor=applied["bg"],
        landcolor=applied["land"],
    )

    os.makedirs(os.path.dirname(output_png), exist_ok=True)
    fig.write_image(output_png, format="png", width=1200, height=600, scale=2)
    if output_html:
        fig.write_html(output_html, include_plotlyjs="cdn")
    return True
