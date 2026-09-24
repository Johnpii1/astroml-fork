class AstroMLError(Exception):
    """Base exception for AstroML"""
    pass

class IngestionError(AstroMLError):
    """Raised for ingestion errors"""
    pass

class FeatureError(AstroMLError):
    """Raised for feature errors"""
    pass

class ModelError(AstroMLError):
    """Raised for model training errors"""
    pass

class DatabaseError(AstroMLError):
    """Raised for database errors"""
    pass
