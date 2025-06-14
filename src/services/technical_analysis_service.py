import pandas as pd
import plotly.graph_objects as go
from ..utils.logging_utils import setup_logger

# Set up logger for this module
logger = setup_logger("TechnicalAnalysisService")

class TechnicalAnalysisService:
    """Service for calculating technical indicators and generating charts."""
    
    def calculate_sma(self, data, window=20):
        """Calculate Simple Moving Average."""
        try:
            return data['Close'].rolling(window=window).mean()
        except Exception as e:
            logger.error(f"Error calculating SMA: {str(e)}")
            return pd.Series(index=data.index)
    
    def calculate_ema(self, data, span=20):
        """Calculate Exponential Moving Average."""
        try:
            return data['Close'].ewm(span=span).mean()
        except Exception as e:
            logger.error(f"Error calculating EMA: {str(e)}")
            return pd.Series(index=data.index)
    
    def calculate_bollinger_bands(self, data, window=20, num_std=2):
        """Calculate Bollinger Bands."""
        try:
            middle_band = self.calculate_sma(data, window)
            std = data['Close'].rolling(window=window).std()
            upper_band = middle_band + (std * num_std)
            lower_band = middle_band - (std * num_std)
            return upper_band, middle_band, lower_band
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            empty = pd.Series(index=data.index)
            return empty, empty, empty
    
    def calculate_vwap(self, data):
        """Calculate Volume Weighted Average Price."""
        try:
            return (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
        except Exception as e:
            logger.error(f"Error calculating VWAP: {str(e)}")
            return pd.Series(index=data.index)
    def create_candlestick_chart(self, data, ticker, indicators=None):
        """Create a candlestick chart with specified indicators."""
        logger.info(f"Creating candlestick chart for {ticker}")
        
        try:
            # Log data information
            logger.debug(f"Data shape: {data.shape}")
            logger.debug(f"Data columns: {list(data.columns)}")
            logger.debug(f"Data index type: {type(data.index)}")
            logger.debug(f"Data date range: {data.index[0]} to {data.index[-1]}")
            
            # Create the base candlestick chart
            logger.debug("Creating candlestick figure...")
            fig = go.Figure(data=[
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name="Candlestick"
                )
            ])
            logger.debug("Candlestick figure created successfully")
            
            # Add selected indicators if provided
            if indicators:
                logger.debug(f"Adding indicators: {indicators}")
                self.add_indicators_to_chart(fig, data, indicators)
                logger.debug("Indicators added successfully")
            
            # Configure chart layout
            logger.debug("Configuring chart layout...")
            fig.update_layout(
                title=f"{ticker} Price Chart",
                xaxis_title="Date",
                yaxis_title="Price",
                xaxis_rangeslider_visible=False
            )
            logger.debug("Chart layout configured successfully")
            
            logger.info(f"Chart created successfully for {ticker}")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating candlestick chart: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return go.Figure()  # Return empty figure on error
    def add_indicators_to_chart(self, fig, data, indicators):
        """Add technical indicators to an existing chart."""
        logger.debug(f"Starting to add {len(indicators)} indicators")
        
        for i, indicator in enumerate(indicators):
            try:
                logger.debug(f"Adding indicator {i+1}/{len(indicators)}: {indicator}")
                
                if indicator == "20-Day SMA":
                    logger.debug("Calculating SMA...")
                    sma = self.calculate_sma(data, 20)
                    logger.debug("Adding SMA trace to chart...")
                    fig.add_trace(go.Scatter(
                        x=data.index, 
                        y=sma, 
                        mode='lines', 
                        name='SMA (20)',
                        line=dict(color='blue')
                    ))
                    logger.debug("SMA trace added successfully")
                    
                elif indicator == "20-Day EMA":
                    logger.debug("Calculating EMA...")
                    ema = self.calculate_ema(data, 20)
                    logger.debug("Adding EMA trace to chart...")
                    fig.add_trace(go.Scatter(
                        x=data.index, 
                        y=ema, 
                        mode='lines', 
                        name='EMA (20)',
                        line=dict(color='orange')
                    ))
                    logger.debug("EMA trace added successfully")
                    
                elif indicator == "Bollinger Bands":
                    logger.debug("Calculating Bollinger Bands...")
                    bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(data, 20, 2)
                    logger.debug("Adding Bollinger Bands traces to chart...")
                    fig.add_trace(go.Scatter(
                        x=data.index, 
                        y=bb_upper, 
                        mode='lines', 
                        name='BB Upper',
                        line=dict(color='green', dash='dash')
                    ))
                    fig.add_trace(go.Scatter(
                        x=data.index, 
                        y=bb_lower, 
                        mode='lines', 
                        name='BB Lower',
                        line=dict(color='red', dash='dash'),
                        fill='tonexty',
                        fillcolor='rgba(0, 100, 80, 0.1)'
                    ))
                    logger.debug("Bollinger Bands traces added successfully")
                    
                elif indicator == "VWAP":
                    logger.debug("Calculating VWAP...")
                    vwap = self.calculate_vwap(data)
                    logger.debug("Adding VWAP trace to chart...")
                    fig.add_trace(go.Scatter(
                        x=data.index, 
                        y=vwap, 
                        mode='lines', 
                        name='VWAP',
                        line=dict(color='purple')
                    ))
                    logger.debug("VWAP trace added successfully")
                    
                logger.debug(f"Added indicator: {indicator} successfully")
                
            except Exception as e:
                logger.error(f"Error adding indicator {indicator}: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                
        logger.debug("Finished adding all indicators")
                
    def generate_technical_data_summary(self, data, ticker, indicators):
        """Generate a text summary of technical indicators."""
        try:
            # Check if this is likely a cryptocurrency
            from ..config.settings import settings
            is_crypto = ticker in settings.CRYPTO_SYMBOLS
            
            # Format large numbers with commas for readability
            current_price = data['Close'].iloc[-1]
            formatted_price = f"${current_price:,.2f}"
            price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
            formatted_change = f"${price_change:,.2f}"
            pct_change = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            high_price = f"${data['High'].max():,.2f}"
            low_price = f"${data['Low'].min():,.2f}"
            
            # Create comprehensive description
            data_description = f"""
            {'Cryptocurrency' if is_crypto else 'Stock'}: {ticker}{'-USD' if is_crypto else ''}
            Date Range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}
            Current Price: {formatted_price}
            Price Change: {formatted_change} ({pct_change:.2f}%)
            52-week High: {high_price}
            52-week Low: {low_price}
            Volume: {data['Volume'].iloc[-1]:,}
            """
            
            # Add technical indicator data to description
            for ind in indicators:
                if ind == "20-Day SMA":
                    sma_value = self.calculate_sma(data, 20).iloc[-1]
                    data_description += f"\n20-Day SMA: ${sma_value:.2f}"
                elif ind == "20-Day EMA":
                    ema_value = self.calculate_ema(data, 20).iloc[-1]
                    data_description += f"\n20-Day EMA: ${ema_value:.2f}"
                elif ind == "Bollinger Bands":
                    _, sma, _ = self.calculate_bollinger_bands(data, 20, 2)
                    std = data['Close'].rolling(window=20).std().iloc[-1]
                    bb_upper = sma.iloc[-1] + 2 * std
                    bb_lower = sma.iloc[-1] - 2 * std
                    data_description += f"\nBollinger Bands: Upper=${bb_upper:.2f}, Middle=${sma.iloc[-1]:.2f}, Lower=${bb_lower:.2f}"
                elif ind == "VWAP":
                    vwap_value = self.calculate_vwap(data).iloc[-1]
                    data_description += f"\nVWAP: ${vwap_value:.2f}"
            
            return data_description
            
        except Exception as e:
            logger.error(f"Error generating technical data summary: {str(e)}")
            return f"Error generating technical data for {ticker}"
