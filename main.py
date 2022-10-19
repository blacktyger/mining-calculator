from email.policy import default

from flaskwebgui import FlaskUI
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from back_end import provider
from back_end.models import *
ORIGINS = ['*']
app = FastAPI()


app.add_middleware(
            CORSMiddleware,
            allow_origins=ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

app.mount("/front_end/static", StaticFiles(directory="front_end/static"), name="static")
templates = Jinja2Templates(directory="front_end/templates")

# ui = FlaskUI(app, start_server='fastapi', width=500, height=900)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/calculate")
async def calculate(parser: Parser):
    rig = Rig(**parser.dict(include={'hashrate', 'algorithm'}))
    currency = Currency(**provider.MarketData().get(parser.currency))
    blockchain = Blockchain(**provider.BlockchainData().get())
    calc = Calculator(rig=rig, blockchain=blockchain, currency=currency, pool_fee=parser.pool_fee)
    print(calc.get_report(as_dict=False).formatted())
    return calc.get_report()


# @app.post("/login/", response_class=HTMLResponse)
# async def login(request: Request, password: str = Form(default=None)):
#     print(GPUtil.showUtilization())
#     context = {"request": request,
#                'password': password,
#                'gpus': GPUtil.getGPUs()[0]}
#     return templates.TemplateResponse("home.html", context)


# if __name__ == "__main__":

