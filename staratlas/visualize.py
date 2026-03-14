import os

import matplotlib.pyplot as plt
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


def render_company_chart(company_counts, output_svg, top_n=10):
    if not company_counts:
        return False
    items = sorted(company_counts.items(), key=lambda item: item[1], reverse=True)[:top_n]
    labels = [item[0].title() for item in items]
    values = [item[1] for item in items]

    os.makedirs(os.path.dirname(output_svg), exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(labels[::-1], values[::-1], color="#2a9d8f")
    ax.set_xlabel("Stargazers")
    ax.set_title("Top Companies")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(output_svg, format="svg")
    plt.close(fig)
    return True


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
