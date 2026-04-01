import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.stock_api import router as stock_router
from app.api.scan_api import router as scan_router
# from app.api.trade_api import router as trade_router

# from app.api.portfolio_api import router as portfolio_router

from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    logger.info("main: Initializing AI Trading Coach Engine...")
    
    try:
        app = FastAPI(
            title="AI Trading Coach Engine",
            description="AI-powered stock analysis and market scanner",
            version="1.0.0"
        )

        #  CORS (important for frontend later)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # later restrict this
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        #  Register routers
        logger.info("main: Registering application routers")
        app.include_router(stock_router, prefix="")
        app.include_router(scan_router, prefix="")
        # app.include_router(trade_router, prefix="")
        # app.include_router(portfolio_router, prefix="")
        
        logger.info("main: Application routers registered successfully.")
        
        @app.get("/")
        async def root():
            return {"status": "online", "message": "AI Trading Coach Engine is running"}

        logger.info("main: FastAPI application startup complete")
        return app

    except Exception as e:
        logger.error(f"Error in main.py at create_app: Application failed to start - {str(e)}")
        raise e


app = create_app()