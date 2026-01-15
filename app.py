import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="SCANNER BDRs - ELITE", layout="wide")

def calcular_indicadores(df):
    df = df.copy()
    stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=14, d=3, smooth_k=3)
    adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
    return pd.concat([df, stoch, adx_df], axis=1).dropna()

def analisar_bdr(ticker):
    try:
        df_diario = yf.download(ticker, period="2y", interval="1d", progress=False)
        if df_diario is None or len(df_diario) < 250: return None
        df_diario.columns = [col[0] if isinstance(col, tuple) else col for col in df_diario.columns]
        
        # SEMANAL
        df_semanal = df_diario.resample('W').last()
        df_s = calcular_indicadores(df_semanal)
        df_s['SMA200'] = ta.sma(df_s['Close'], length=200)
        s = df_s.iloc[-1]
        
        semanal_ok = (s['Close'] > s['SMA200']) and (s['STOCHk_14_3_3'] > s['STOCHd_14_3_3']) and \
                     (s['DMP_14'] > s['DMN_14']) and (s['ADX_14'] > 15)
        
        if not semanal_ok: return None

        # DIÁRIO
        df_d = calcular_indicadores(df_diario)
        d_atual = df_d.iloc[-1]
        d_anterior = df_d.iloc[-2]
        
        dmi_ok = (d_atual['DMP_14'] > d_atual['DMN_14']) and (d_atual['ADX_14'] > 15)
        cruzou_hoje = (d_atual['STOCHk_14_3_3'] > d_atual['STOCHd_14_3_3']) and \
                      (d_anterior['STOCHk_14_3_3'] <= d_anterior['STOCHd_14_3_3'])
        gatilho_ok = cruzou_hoje and (d_atual['STOCHk_14_3_3'] <= 35)

        if dmi_ok and gatilho_ok:
            return {"Preço": round(float(d_atual['Close']), 2), "ADX": round(d_atual['ADX_14'], 1), "K": round(d_atual['STOCHk_14_3_3'], 1)}
        return None
    except:
        return None

def main():
    st.title("🌍 Scanner BDRs - Swing Trade")
    st.write("Filtro: Semanal (Alta) + Diário (Gatilho < 35)")

    bdrs_top = [
        "AAPL34.SA", "AMZO34.SA", "GOGL34.SA", "MSFT34.SA", "TSLA34.SA", "META34.SA", "NFLX34.SA", "NVDC34.SA", "MELI34.SA", "BABA34.SA",
        "DISB34.SA", "PYPL34.SA", "JNJB34.SA", "PGCO34.SA", "HOME34.SA", "COCA34.SA", "MCDC34.SA", "NIKE34.SA", "NUBR33.SA", "VZBO34.SA",
        "BERK34.SA", "JPMC34.SA", "VISA34.SA", "WMTB34.SA", "XOMP34.SA", "ORCL34.SA", "PEP34.SA", "PFIZ34.SA", "SBUB34.SA", "TGTB34.SA"
    ]

    if st.button('🌍 Iniciar Varredura de BDRs'):
        hits = []
        barra = st.progress(0)
        for i, t in enumerate(bdrs_top):
            res = analisar_bdr(t)
            if res:
                hits.append({"BDR": t.replace(".SA", ""), "PREÇO": res["Preço"], "ADX": res["ADX"], "STOCH_K": res["K"]})
            barra.progress((i + 1) / len(bdrs_top))
        
        if hits:
            st.table(pd.DataFrame(hits))
        else:
            st.info("Nenhum BDR com gatilho técnico agora.")

if __name__ == "__main__":
    main()
