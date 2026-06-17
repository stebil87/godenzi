import streamlit as st

LOGO_PATH = "godenzi.png"


def mostra_logo():
    col_logo, col_titolo = st.columns([1, 4])
    with col_logo:
        st.image(LOGO_PATH, width=120)
    with col_titolo:
        st.markdown(
            """
            <div style="padding-top: 25px;">
                <span style="font-size: 1.1em; font-weight: bold;">IVO GODENZI &nbsp; LATTONIERE</span><br>
                <span>RIVA S. VITALE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.divider()
