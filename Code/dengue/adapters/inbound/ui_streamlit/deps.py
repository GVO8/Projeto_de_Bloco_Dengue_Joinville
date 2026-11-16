"""Fornece o gateway às páginas. Os testes substituem `obter_gateway` por um gateway falso."""

import streamlit as st

from dengue.adapters.inbound.ui_streamlit.gateways import ApiGateway, Gateway, GatewayComAlternativa, LocalGateway
from dengue.container import Container


@st.cache_resource
def obter_gateway() -> Gateway:
    c = Container()
    return GatewayComAlternativa(ApiGateway(c.config.api_url), LocalGateway(c))
