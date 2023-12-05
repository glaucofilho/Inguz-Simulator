from datetime import date, datetime, timedelta

import pandas as pd
import pvlib


def generate_irradiance(
    date: date = None,
    tz="America/Sao_Paulo",
    freq_ms: int = 60 * 1000,
    latitude: float = -21.289507,
    longitude: float = -46.697519,
    altitude: float = 835.0,
    pressure: float = 1006.4,
    temperature: float = 25.0,
):
    start_time = datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=tz,
    )
    end_time = datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        hour=23,
        minute=59,
        second=59,
        microsecond=999999,
        tzinfo=tz,
    )
    times = pd.date_range(
        start=start_time,
        end=end_time,
        freq=timedelta(milliseconds=freq_ms),
        tz=tz,
    )
    solpos = pvlib.solarposition.get_solarposition(
        time=times,
        latitude=latitude,
        longitude=longitude,
        temperature=temperature,
        altitude=altitude,
    )
    dni_extra = pvlib.irradiance.get_extra_radiation(times)
    solpos["airmass_absolute"] = pvlib.atmosphere.get_absolute_airmass(
        solpos["apparent_zenith"], pressure
    )
    clearsky = pvlib.clearsky.ineichen(
        apparent_zenith=solpos["apparent_zenith"],
        airmass_absolute=solpos["airmass_absolute"],
        dni_extra=dni_extra,
        altitude=altitude,
        linke_turbidity=3.0,
    )
    irradiance = pvlib.irradiance.get_total_irradiance(
        surface_tilt=0,
        surface_azimuth=0,
        solar_zenith=solpos["apparent_zenith"],
        solar_azimuth=solpos["azimuth"],
        dni=clearsky["dni"],
        ghi=clearsky["ghi"],
        dhi=clearsky["dhi"],
    )

    result_df = pd.DataFrame(
        {
            "Timestamp": times,
            "GHI": clearsky["ghi"].values,
            "POA_Total": irradiance["poa_global"].values,
            "POA_Direct": irradiance["poa_direct"].values,
            "POA_Diffuse": irradiance["poa_diffuse"].values,
        }
    )
    div_kw_hour = 1000.0 * (1 * 60 * 60000) / freq_ms
    result_df["AC_GHI"] = result_df["GHI"].cumsum() / div_kw_hour
    result_df["AC_POA_Total"] = result_df["POA_Total"].cumsum() / div_kw_hour
    result_df["AC_POA_Direct"] = result_df["POA_Direct"].cumsum() / div_kw_hour
    result_df["AC_POA_Diffuse"] = result_df["POA_Diffuse"].cumsum() / div_kw_hour

    return result_df


# df = generate_irradiance()
# with pd.option_context("display.max_rows", None, "display.max_columns", None):
#     print(df)
