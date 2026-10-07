import zipfile
from pathlib import Path
from typing import List
from app.core.config import settings
from app.core.logging import logger


class ZipService:
    @staticmethod
    def create_job_zip(job_id: str, pdf_paths: List[str]) -> Path:
        """
        Compress all successful certificate PDFs into a single ZIP archive.
        Returns the Path to the generated ZIP archive.
        """
        job_dir = settings.STORAGE_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        zip_path = job_dir / f"certificates_{job_id}.zip"

        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path_str in pdf_paths:
                file_path = Path(path_str)
                if file_path.exists() and file_path.is_file():
                    # Archive with just the filename, not full nested path
                    archive.write(file_path, arcname=file_path.name)
                else:
                    logger.warning(
                        f"PDF file not found during ZIP generation: {path_str}",
                        extra={"job_id": job_id}
                    )

        logger.info(
            f"Created ZIP archive with {len(archive.namelist())} certificates",
            extra={"job_id": job_id}
        )
        return zip_path
