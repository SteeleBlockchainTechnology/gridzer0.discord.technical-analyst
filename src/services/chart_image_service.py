import io
from ..utils.logging_utils import setup_logger
import kaleido

# Set up logger for this module
logger = setup_logger("ChartImageService")

class ChartImageService:
    """Service for generating static chart images from Plotly figures using Plotly's native kaleido export."""
    
    def __init__(self, width=1200, height=800):
        """
        Initialize the chart image service.
        
        Args:
            width: Default image width in pixels
            height: Default image height in pixels
        """
        self.width = width
        self.height = height
        logger.info("Plotly-based ChartImageService initialized successfully")
    
    def export_chart_as_image(self, fig, width=None, height=None):
        """Export Plotly figure as PNG image bytes using Plotly's native kaleido export."""
        if width is None:
            width = self.width
        if height is None:
            height = self.height
            
        logger.debug(f"Exporting chart as PNG image using Plotly kaleido (size: {width}x{height})")
        logger.debug(f"Figure has {len(fig.data)} traces")
        
        try:
            # Set the figure size
            logger.debug("Setting figure layout...")
            fig.update_layout(
                width=width,
                height=height,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            logger.debug("Figure layout updated")
            
            # Export to PNG bytes using kaleido
            logger.debug("Starting image conversion with kaleido...")
            img_bytes = fig.to_image(format="png", width=width, height=height, engine="kaleido")
            logger.debug(f"Image conversion completed. Size: {len(img_bytes)} bytes")
            
            # Convert to BytesIO
            logger.debug("Converting to BytesIO...")
            img_buffer = io.BytesIO(img_bytes)
            img_buffer.seek(0)
            
            logger.debug("Plotly kaleido export successful")
            return img_buffer
            
        except Exception as e:
            logger.error(f"Plotly kaleido export failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def set_dimensions(self, width, height):
        """
        Update default image dimensions.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
        """
        self.width = width
        self.height = height
        logger.info(f"Updated dimensions to {width}x{height}")
