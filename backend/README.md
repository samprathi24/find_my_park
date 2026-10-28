\# FindMyPark Backend



\## Overview

FindMyPark predicts future parking occupancy to help users estimate parking availability.



The backend uses FastAPI to expose a REST API and an XGBoost regression model to forecast occupancy approximately 60 minutes ahead.



\## Prediction Model

\- \*\*Algorithm:\*\* XGBoost Regressor

\- \*\*Forecast horizon:\*\* Approximately 60 minutes

\- \*\*Training dataset:\*\* Birmingham parking occupancy dataset

\- \*\*Evaluation metrics on the test split:\*\*

&#x20; - MAE: 37.49 spaces

&#x20; - RMSE: 70.41 spaces



These are preliminary results from the Birmingham dataset and do not represent validated performance on Bengaluru parking data.



\## Prediction API



\*\*Endpoint:\*\* `POST /api/predict`



The endpoint accepts:

\- `location`: Parking location identifier

\- `capacity`: Total parking capacity

\- `hour`: Hour of the day

\- `day\_of\_week`: Day of the week

\- `month`: Month number

\- `is\_weekend`: `1` for weekend, otherwise `0`

\- `current\_occupancy`: Current number of occupied spaces



Example request:



```json

{

&#x20; "location": "BHMBCCMKT01",

&#x20; "capacity": 577,

&#x20; "hour": 9,

&#x20; "day\_of\_week": 1,

&#x20; "month": 10,

&#x20; "is\_weekend": 0,

&#x20; "current\_occupancy": 306

}

```



The response includes predicted occupancy, estimated available spaces, capacity, and the forecast horizon.



\## Running the Backend



Run these commands from the `backend` directory after setting up the Python environment and installing dependencies:



```bash

python -m uvicorn app.main:app --reload

```



Open the interactive API documentation at:



`http://127.0.0.1:8000/docs`



\## Model Files



The prediction module uses the following trained artifacts:



\- `app/ml/prediction/findmypark\_xgboost\_60min.pkl`

\- `app/ml/prediction/findmypark\_preprocessor\_60min.pkl`



Both files must be available at the paths expected by the prediction code.



\## Current Limitations



\- The model was trained on Birmingham parking data.

\- Predictions have not yet been validated on Bengaluru parking data.

\- Current occupancy is supplied to the API; integration with the YOLO vehicle-counting module is a planned step.

\- Estimated available spaces are calculated from capacity minus predicted occupancy and should be bounded between zero and capacity.



