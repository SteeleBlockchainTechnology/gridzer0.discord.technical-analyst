import pandas as pd
import plotly.graph_objects as go
import io
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
            # Create the base candlestick chart
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
            
            # Add selected indicators if provided
            if indicators:
                self.add_indicators_to_chart(fig, data, indicators)
              # Configure chart layout
            fig.update_layout(
                title=f"{ticker} Price Chart",
                xaxis_title="Date",
                yaxis_title="Price",
                xaxis_rangeslider_visible=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating candlestick chart: {str(e)}")
            return go.Figure()  # Return empty figure on error
    
    def add_indicators_to_chart(self, fig, data, indicators):
        """Add technical indicators to an existing chart."""

        for indicator in indicators:
            try:
                logger.debug(f"Adding indicator: {indicator}")
                
                if indicator == "20-Day SMA":
                    sma = self.calculate_sma(data, 20)
                    fig.add_trace(go.Scatter(
                        x=data.index, 
                        y=sma, 
                        mode='lines', 
                        name='SMA (20)',
                        line=dict(color='blue')
                    ))
                    
                elif indicator == "20-Day EMA":
                    ema = self.calculate_ema(data, 20)
                    fig.add_trace(go.Scatter(
                        x=data.index, 
                        y=ema, 
                        mode='lines', 
                        name='EMA (20)',
                        line=dict(color='orange')
                    ))
                    
                elif indicator == "Bollinger Bands":
                    bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(data, 20, 2)
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
                    
                elif indicator == "VWAP":
                    vwap = self.calculate_vwap(data)
                    fig.add_trace(go.Scatter(
                        x=data.index, 
                        y=vwap, 
                        mode='lines', 
                        name='VWAP',
                        line=dict(color='purple')
                    ))
                    
                logger.debug(f"Added indicator: {indicator} successfully")
                
            except Exception as e:
                logger.error(f"Error adding indicator {indicator}: {str(e)}")
                
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
    
    def export_chart_as_image(self, fig, width=1200, height=800):
        """Export Plotly figure as PNG image bytes using PIL as primary generator."""
        logger.debug("Exporting chart as PNG image using PIL")
        
        try:
            # First try to get the figure as HTML and convert to image using PIL
            return self._create_chart_image_with_pil(fig, width, height)
            
        except Exception as e:
            logger.error(f"PIL chart generation failed: {e}")
            # Create fallback image
            return self._create_fallback_image(width, height)
    
    def _create_chart_image_with_pil(self, fig, width=800, height=600):
        """Create chart image using PIL from Plotly figure data."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            
            logger.debug(f"Creating chart image with PIL ({width}x{height})")
            
            # Create a white background
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font
            try:
                title_font = ImageFont.truetype("arial.ttf", 16)
                text_font = ImageFont.truetype("arial.ttf", 12)
            except:
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
            
            # Get the first candlestick trace (should be the main data)
            candlestick_data = None
            for trace in fig.data:
                if hasattr(trace, 'open') and hasattr(trace, 'high'):
                    candlestick_data = trace
                    break
            
            if candlestick_data:
                # Extract OHLC data
                dates = candlestick_data.x
                opens = candlestick_data.open
                highs = candlestick_data.high
                lows = candlestick_data.low
                closes = candlestick_data.close
                
                # Calculate chart area (leave margins for title and labels)
                margin_top = 50
                margin_bottom = 50
                margin_left = 80
                margin_right = 50
                
                chart_width = width - margin_left - margin_right
                chart_height = height - margin_top - margin_bottom
                
                # Find price range
                all_prices = list(highs) + list(lows)
                min_price = min(all_prices)
                max_price = max(all_prices)
                price_range = max_price - min_price
                
                if price_range == 0:
                    price_range = 1  # Avoid division by zero
                
                # Draw title
                title = fig.layout.title.text if fig.layout.title else "Price Chart"
                title_bbox = draw.textbbox((0, 0), title, font=title_font)
                title_width = title_bbox[2] - title_bbox[0]
                title_x = (width - title_width) // 2
                draw.text((title_x, 10), title, fill='black', font=title_font)
                
                # Draw chart border
                chart_x1 = margin_left
                chart_y1 = margin_top
                chart_x2 = margin_left + chart_width
                chart_y2 = margin_top + chart_height
                draw.rectangle([chart_x1, chart_y1, chart_x2, chart_y2], outline='black', width=1)
                
                # Draw candlesticks (simplified as rectangles)
                num_candles = len(closes)
                if num_candles > 0:
                    candle_width = max(1, chart_width // (num_candles * 2))
                    
                    for i in range(num_candles):
                        if i >= len(opens) or i >= len(closes):
                            continue
                            
                        open_price = opens[i]
                        close_price = closes[i]
                        high_price = highs[i]
                        low_price = lows[i]
                        
                        if any(pd.isna([open_price, close_price, high_price, low_price])):
                            continue
                        
                        # Calculate positions
                        x = margin_left + (i * chart_width // num_candles)
                        
                        # Normalize prices to chart coordinates
                        open_y = margin_top + chart_height - int(((open_price - min_price) / price_range) * chart_height)
                        close_y = margin_top + chart_height - int(((close_price - min_price) / price_range) * chart_height)
                        high_y = margin_top + chart_height - int(((high_price - min_price) / price_range) * chart_height)
                        low_y = margin_top + chart_height - int(((low_price - min_price) / price_range) * chart_height)
                        
                        # Choose color (green for up, red for down)
                        color = 'green' if close_price >= open_price else 'red'
                        
                        # Draw high-low line
                        draw.line([(x + candle_width//2, high_y), (x + candle_width//2, low_y)], fill='black', width=1)
                        
                        # Draw body rectangle
                        body_top = min(open_y, close_y)
                        body_bottom = max(open_y, close_y)
                        draw.rectangle([x, body_top, x + candle_width, body_bottom], fill=color, outline='black')
                
                # Add price labels on Y-axis
                num_labels = 5
                for i in range(num_labels + 1):
                    price = min_price + (price_range * i / num_labels)
                    y = margin_top + chart_height - int((i / num_labels) * chart_height)
                    price_text = f"${price:.2f}"
                    draw.text((5, y-6), price_text, fill='black', font=text_font)
                  # Add technical indicators note
                indicator_traces = [trace for trace in fig.data if hasattr(trace, 'mode') and trace.mode == 'lines']
                if indicator_traces:
                    indicators_text = f"Chart includes {len(indicator_traces)} technical indicators:"
                    draw.text((margin_left, height-50), indicators_text, fill='blue', font=text_font)
                    
                    # List the indicators
                    for i, trace in enumerate(indicator_traces):
                        indicator_name = trace.name if hasattr(trace, 'name') else f"Indicator {i+1}"
                        indicator_color = trace.line.color if hasattr(trace, 'line') and hasattr(trace.line, 'color') else 'blue'
                        draw.text((margin_left + 10, height-35 + i*12), f"• {indicator_name}", fill=indicator_color, font=text_font)
                        
                        # Draw a simple line representation of the indicator
                        if hasattr(trace, 'y') and len(trace.y) > 0:
                            try:
                                # Get indicator values and normalize them
                                indicator_values = [v for v in trace.y if not pd.isna(v)]
                                if len(indicator_values) > 1:
                                    # Draw simplified indicator line
                                    prev_x = None
                                    prev_y = None
                                    for j, value in enumerate(indicator_values[-min(50, len(indicator_values)):]):  # Show last 50 points
                                        x = margin_left + (j * chart_width // min(50, len(indicator_values)))
                                        y = margin_top + chart_height - int(((value - min_price) / price_range) * chart_height)
                                        
                                        if prev_x is not None and prev_y is not None:
                                            draw.line([(prev_x, prev_y), (x, y)], fill=indicator_color, width=2)
                                        
                                        prev_x = x
                                        prev_y = y
                            except Exception as e:
                                logger.debug(f"Could not draw indicator line for {indicator_name}: {e}")
            
            else:
                # No candlestick data found, create a simple placeholder
                text = "Chart Data Processing\nTechnical Analysis Available"
                text_bbox = draw.textbbox((0, 0), text, font=title_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                draw.text((x, y), text, fill='black', font=title_font)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            logger.debug("PIL chart image created successfully")
            return img_buffer
            
        except Exception as e:
            logger.error(f"Failed to create PIL chart image: {e}")
            raise

    def _create_fallback_image(self, width=800, height=600):
        """Create a fallback image when Plotly export fails."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            logger.debug("Creating fallback image with PIL")
            
            # Create a simple image with text
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Draw text
            text = "Chart Export Failed\nUsing Fallback Image\nTechnical Analysis Available in Text"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x, y), text, fill='black', font=font)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            logger.debug("Fallback image created successfully")
            return img_buffer
            
        except Exception as e:
            logger.error(f"Failed to create fallback image: {e}")
            return None
