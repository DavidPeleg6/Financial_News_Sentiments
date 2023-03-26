# this is for testing model generation...

import model
import datetime

model.generate_models(["MSFT", "AAPL"], overwrite_mode=model.overwrite_modes.ALWAYS, test_months=1)
model.predict_tomorrow(["MSFT"], datetime.datetime.now)