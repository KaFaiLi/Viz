# special rules for handling specific mother metrics
special_metric_rules = {
    "VaR": {
        "include_pattern": r"^(VaR|SVaR|STTH)", # Include only VaR, SVaR, and STTHH
    },
    "FTQ": {
        "include_pattern": r"^FTQ(\d+[DWMY])?", # Include FTQ and sub-metrics like FTQ3M, FTQ1Y, etc.
        "exclude_pattern": r"(globJapan|Japan)(\d+[DWMY])?", # Exclude FTQglobJapan and its sub-metrics like FTQglobJapan1M, FTQglobJapan5Y, etc.
    },
    "IRSensi": {
        "include_pattern": r"^IRSensi(\d+[DWMY])?", # Include only IRSensi and sub-metrics with maturity
        "exclude_pattern": r"(JPY|ByCurve)(\d+[DWMY])?", # Exclude unrelated metrics like IRSensiJPY, IRSensiDeliverableJPYByCurve
    },
    "FX": {
        "include_pattern": r"^FX[A-Z]{3}", # Include FX and FXEUR, FXJPY, FXUSD, etc.
    },
    "CIMSensiBOR": {
        "include_pattern": r"^CIMSensiBOR(\d+[DWMY])?",
        "exclude_pattern": r"(EUR)(\d+[DWMY])?", #TODO it still having CIMSensiBOREUR1W CIMSensiBOREUR1M
    },
}