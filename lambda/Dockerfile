FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
ADD Util/ Util
ADD Util/ RGScraper
ADD Util/ Common
ADD RGScraper/ RGScraper
ADD Sportsbook/ Sportsbook
ADD Sportsbook/Pinnacle Pinnacle
ADD Sportsbook/Pinnacle PinnacleUtil
COPY Sportsbook/Pinnacle/SavePinnacleOdds.py ${LAMBDA_TASK_ROOT}
ADD Sportsbook/Draftkings Draftkings
ADD Sportsbook/Draftkings DraftkingsUtil
COPY Sportsbook/Draftkings/SaveDraftkingsOdds.py ${LAMBDA_TASK_ROOT}
ADD Sportsbook/Espn Espn
ADD Sportsbook/Espn EspnUtil
COPY Sportsbook/Espn/SaveEspnOdds.py ${LAMBDA_TASK_ROOT}
ADD Sportsbook/EV EV
ADD Sportsbook/EV EVUtil
ADD Sportsbook/EV OddsUtil
COPY Sportsbook/EV/GetEV.py ${LAMBDA_TASK_ROOT}
COPY Sportsbook/EV/GetPlusEvPlays.py ${LAMBDA_TASK_ROOT}
COPY Sportsbook/EV/GetLatestSavedOdds.py ${LAMBDA_TASK_ROOT}
COPY Sportsbook/Pinnacle/AggregateBets.py ${LAMBDA_TASK_ROOT}
ADD Sportsbook/Fanduel Fanduel
ADD Sportsbook/Fanduel FanduelUtil
COPY Sportsbook/Fanduel/SaveFanduelOdds.py ${LAMBDA_TASK_ROOT}
# COPY Sportsbook/Fanduel/AggregateBets.py ${LAMBDA_TASK_ROOT}
COPY Sportsbook/SaveOddsInvoker.py ${LAMBDA_TASK_ROOT}
COPY Sportsbook/GetEvents.py ${LAMBDA_TASK_ROOT}
COPY Sportsbook/GetEventsList.py ${LAMBDA_TASK_ROOT}
COPY Sportsbook/GetEventOdds.py ${LAMBDA_TASK_ROOT}
COPY Sportsbook/SaveOdds.py ${LAMBDA_TASK_ROOT}
COPY Sportsbook/ScheduleOddsScraping.py ${LAMBDA_TASK_ROOT}
COPY Sportsbook/CreatePropsCsv.py ${LAMBDA_TASK_ROOT}
COPY GetContestStructure.py ${LAMBDA_TASK_ROOT}
COPY RGScraper/GetSlateNames.py ${LAMBDA_TASK_ROOT}
COPY RGScraper/GetSlate.py ${LAMBDA_TASK_ROOT}
COPY RGScraper/GetSlateCSV.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the xDockerfile)
CMD [ "GetContestStructure.handler" ]