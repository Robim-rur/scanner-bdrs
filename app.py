import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="SCANNER BDRs - ELITE EMA 69", layout="wide")

def calcular_indicadores(df):
    df = df.copy()
    # Estocástico 14,3,3
    stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=14, d=3, smooth_k=3)
    # DMI/ADX 14
    adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
    return pd.concat([df, stoch, adx_df], axis=1).dropna()

def analisar_bdr(ticker):
    try:
        # Puxa histórico necessário
        df_diario = yf.download(ticker, period="2y", interval="1d", progress=False)
        if df_diario is None or len(df_diario) < 150: return None
        df_diario.columns = [col[0] if isinstance(col, tuple) else col for col in df_diario.columns]
        
        # --- FILTRO 1: SEMANAL (USANDO EMA 69) ---
        df_semanal = df_diario.resample('W').last()
        df_s = calcular_indicadores(df_semanal)
        # Sua nova regra de ouro: EMA 69
        df_s['EMA69'] = ta.ema(df_s['Close'], length=69)
        s = df_s.iloc[-1]
        
        # Filtros Semanal: Preço > EMA69 + Estocástico K>D + DMI Positivo
        semanal_ok = (s['Close'] > s['EMA69']) and \
                     (s['STOCHk_14_3_3'] > s['STOCHd_14_3_3']) and \
                     (s['DMP_14'] > s['DMN_14']) and \
                     (s['ADX_14'] > 15)
        
        if not semanal_ok: return None

        # --- FILTRO 2: DIÁRIO (GATILHO ESTOCÁSTICO < 35) ---
        df_d = calcular_indicadores(df_diario)
        d_atual = df_d.iloc[-1]
        d_anterior = df_d.iloc[-2]
        
        # DMI Diário
        dmi_ok = (d_atual['DMP_14'] > d_atual['DMN_14']) and (d_atual['ADX_14'] > 15)
        
        # Gatilho: Cruzamento hoje + valor de K <= 35
        cruzou_hoje = (d_atual['STOCHk_14_3_3'] > d_atual['STOCHd_14_3_3']) and \
                      (d_anterior['STOCHk_14_3_3'] <= d_anterior['STOCHd_14_3_3'])
        gatilho_ok = cruzou_hoje and (d_atual['STOCHk_14_3_3'] <= 35)

        if dmi_ok and gatilho_ok:
            return {
                "Preço": round(float(d_atual['Close']), 2), 
                "ADX": round(d_atual['ADX_14'], 1), 
                "K": round(d_atual['STOCHk_14_3_3'], 1),
                "EMA69_S": round(float(s['EMA69']), 2)
            }
        return None
    except:
        return None

def main():
    st.title("🌍 Scanner BDRs - Setup EMA 69")
    st.write("Filtros: Semanal (Acima EMA 69 + DMI + Estoch) | Diário (DMI + Gatilho < 35)")

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
                hits.append({
                    "BDR": t.replace(".SA", ""), 
                    "PREÇO": res["Preço"], 
                    "ADX_D": res["ADX"], 
                    "STOCH_K": res["K"],
                    "EMA 69 (Semanal)": res["EMA69_S"]
                })
            barra.progress((i + 1) / len(bdrs_top))
        
        if hits:
            st.table(pd.DataFrame(hits))
        else:
            st.info("Nenhum BDR cumpre os critérios (Preço > EMA 69 Semanal + Gatilho Diário < 35).")

if __name__ == "__main__":
    main()
