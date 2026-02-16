"""
Board Service - 게시글 비즈니스 로직
이미지 업로드 포함
"""
import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from models import Board, BoardImg
from utils import Util
from exceptions import (
    FileUploadException, 
    InvalidFileExtensionException, 
    FileSizeLimitException,
    NotFoundException
)
from dotenv import load_dotenv # 로컬 개발일때  + .env 사용
load_dotenv(override=True) # .env 파일 명시적 로드 (최우선)

class BoardService:
    """게시판 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # 환경 변수에서 설정 가져오기
        self.upload_dir = os.getenv("UPLOAD_DIR", "/mnt/user-data/uploads")
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
        self.max_images = int(os.getenv("MAX_IMAGES_PER_POST", "5"))
        self.allowed_extensions = os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif,webp").split(",")
    
    
    def create_board(
        self, 
        board_title: str,
        board_content: str,
        member_no: int,
        board_code: int = 3,
        images: List[UploadFile] = None
    ) -> Board:
        """
        게시글 작성
        
        Args:
            board_title: 제목
            board_content: 내용 (XSS 처리)
            member_no: 작성자 번호
            board_code: 게시판 코드 (기본값: 3 = 자유게시판)
            images: 업로드 이미지 파일 리스트 (최대 5개)
            
        Returns:
            생성된 Board 객체
            
        Raises:
            FileUploadException: 파일 업로드 실패
            InvalidFileExtensionException: 잘못된 파일 확장자
            FileSizeLimitException: 파일 크기 초과
        """
        
        temp_files: list[Path] = []
        
        try:
            # 1. XSS 방지 처리
            board_title = Util.xss_handling(board_title)
            board_content = Util.xss_handling(board_content)
            
            # =============================
            # 2. 게시글 DB 저장 (DB 트랜잭션)
            # =============================
            with self.db.begin():
                
                new_board = Board(
                    board_title=board_title,
                    board_content=board_content,
                    board_code=board_code,
                    member_no=member_no
                )
                
                self.db.add(new_board)
                self.db.flush()  # board_no 생성을 위해 flush
                
                # 3. 이미지 업로드 처리(# 이미지 임시 업로드)
                if images:
                    temp_files = self._upload_images_temp(
                        board_no=new_board.board_no,
                        images=images
                    )
                    # 이미지 DB 저장
                    self._save_image_metadata(
                        board_no=new_board.board_no,
                        temp_files=temp_files, # for img_path & img_rename
                        images=images # for img_orig by original_filename = Util.sanitize_filename(image.filename) for image in images
                    )            
            
            # =============================
            # 4. 커밋 (commit 성공 이후)
            # =============================
            self._finalize_images(temp_files)
            
            self.db.refresh(new_board)
            
            return new_board
        
        except Exception as e:
            # rollback + temp 파일 제거
            self.db.rollback()   # Exception 발생시 transactional(rollback)처리
            self._delete_temp_files(temp_files)
            raise e              # 예외는 상위로 전달    
    
        
    def _upload_images_temp(
        self,
        board_no: int,
        images: List[UploadFile]
    ) -> List[Path]:
        """_summary_
        임시 이미지 업로드

        Args:
            board_no (int): _description_
            images (List[UploadFile]): _description_

        Raises:
            FileUploadException: _description_
            InvalidFileExtensionException: _description_
            FileSizeLimitException: _description_
            FileUploadException: _description_
            FileUploadException: _description_
            InvalidFileExtensionException: _description_
            FileSizeLimitException: _description_
            FileUploadException: _description_
            NotFoundException: _description_
            ForbiddenException: _description_
            FileUploadException: _description_
            e: _description_
            InvalidFileExtensionException: _description_
            FileUploadException: _description_

        Returns:
            List[Path]: _description_
        """
        if len(images) > self.max_images:
            raise FileUploadException(
                f"이미지는 최대 {self.max_images}개까지 업로드 가능합니다."
            )

        # img_path=f"/images/board/freeboard/", # "/boards/{board_no}/{renamed_filename}" => "/images/board/freeboard/"
        #temp_dir = Path(self.upload_dir) / "temp" / "boards" / str(board_no)# 각 게시글별 업로드 이미지관리 폴더 생성한 경우
        temp_dir = Path(self.upload_dir) / "temp" / "images/board/freeboard" # 현 oracle Board_Img 데이터베이스에 맞게
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_files = []

        for idx, image in enumerate(images):
            original_filename = Util.sanitize_filename(image.filename)

            if not Util.validate_image_extension(original_filename, self.allowed_extensions):
                raise InvalidFileExtensionException(
                    f"허용되지 않은 파일 형식입니다. ({original_filename})"
                )

            if image.size and image.size > self.max_file_size:
                max_mb = self.max_file_size / (1024 * 1024)
                raise FileSizeLimitException(
                    f"파일 크기는 {max_mb}MB를 초과할 수 없습니다. ({original_filename})"
                )

            renamed_filename = Util.file_rename_uuid(original_filename)
            save_path = temp_dir / renamed_filename # Path(self.upload_dir) / "temp" / "images/board/freeboard"/ renamed_filename

            try:
                with save_path.open("wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)

                temp_files.append(save_path)

            except Exception as e:
                if save_path.exists():
                    save_path.unlink()
                raise FileUploadException(f"파일 업로드 중 오류 발생: {str(e)}")

        return temp_files
        
    # 이미지 메타데이터 DB 저장    
    def _save_image_metadata(self, board_no: int, 
                            temp_files: list[Path],
                            images: List[UploadFile]): 
                                                    
        for idx, temp_path in enumerate(temp_files):
                                                
            # 원본 파일명 for img_orig
            img = images[idx]
            original_filename = Util.sanitize_filename(img.filename)
            
            # for img_path
            print("########### img_path calc: ", str(temp_path.parent).replace(f"{self.upload_dir}/temp", ""))
            # 이미지 객체 생성
            board_img = BoardImg(
                img_path=str(temp_path.parent).replace(f"{self.upload_dir}/temp", "") + "/",
                img_orig=original_filename,
                img_rename=temp_path.name, # temp_path는 Path()객체, 파일명
                img_order=idx,
                board_no=board_no
            )
            self.db.add(board_img)

    # commit 후 파일 확정 이동
    def _finalize_images(self, temp_files: list[Path]):

        for temp_path in temp_files:
            final_path = Path(
                str(temp_path).replace("/temp", "")
            )
            final_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(temp_path, final_path)

    # 실패 시 임시 파일 정리
    def _delete_temp_files(self, temp_files: list[Path]):
        for path in temp_files:
            if path.exists():
                path.unlink()

    
    def _upload_images(self, board_no: int, images: List[UploadFile]) -> List[BoardImg]:
        """
        게시글 이미지 업로드
        
        Args:
            board_no: 게시글 번호
            images: 업로드 파일 리스트
            
        Returns:
            생성된 BoardImg 객체 리스트
            
        Raises:
            FileUploadException: 파일 업로드 실패
            InvalidFileExtensionException: 잘못된 확장자
            FileSizeLimitException: 파일 크기 초과
        """
        
        # 이미지 개수 검증
        if len(images) > self.max_images:
            raise FileUploadException(f"이미지는 최대 {self.max_images}개까지 업로드 가능합니다.")
        
        board_images = []
        
        for idx, image in enumerate(images):
            # 파일명 안전하게 처리
            original_filename = Util.sanitize_filename(image.filename)
            
            # 확장자 검증
            if not Util.validate_image_extension(original_filename, self.allowed_extensions):
                raise InvalidFileExtensionException(
                    f"허용되지 않은 파일 형식입니다. ({original_filename})"
                )
            
            # 파일 크기 검증
            if image.size and image.size > self.max_file_size:
                max_mb = self.max_file_size / (1024 * 1024)
                raise FileSizeLimitException(
                    f"파일 크기는 {max_mb}MB를 초과할 수 없습니다. ({original_filename})"
                )
            
            # 파일명 변경 (중복 방지)
            renamed_filename = Util.file_rename_uuid(original_filename)
            
            # 저장 경로 생성
            save_dir = Path(self.upload_dir) / "boards" / str(board_no)
            save_dir.mkdir(parents=True, exist_ok=True)
            
            save_path = save_dir / renamed_filename
            
            try:
                # 파일 저장
                with save_path.open("wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
                
                # DB에 이미지 정보 저장
                board_img = BoardImg(
                    img_path=f"/images/board/freeboard/",   
                    img_orig=original_filename,
                    img_rename=renamed_filename,
                    img_order=idx,  # 0: 썸네일, 1~4: 서브 이미지
                    board_no=board_no
                )
                
                self.db.add(board_img)
                board_images.append(board_img)
                
            except Exception as e:
                # 업로드 실패 시 이미 저장된 파일 삭제
                if save_path.exists():
                    save_path.unlink()
                raise FileUploadException(f"파일 업로드 중 오류 발생: {str(e)}")
        
        return board_images
    
    
    def update_board(
        self,
        board_no: int,
        board_title: str,
        board_content: str,
        member_no: int,
        delete_image_orders: List[int] = None,
        new_images: List[UploadFile] = None
    ) -> Board:
        """
        게시글 수정
        
        Args:
            board_no: 게시글 번호
            board_title: 수정할 제목
            board_content: 수정할 내용
            member_no: 수정 요청자 (권한 검증용)
            delete_image_orders: 삭제할 이미지 순서 리스트
            new_images: 새로 추가할 이미지 리스트
            
        Returns:
            수정된 Board 객체
            
        Raises:
            NotFoundException: 게시글 없음
            ForbiddenException: 권한 없음
        """
        from exceptions import ForbiddenException
        from datetime import datetime
        
        uploaded_files = []      # 새로 업로드된 파일 (rollback 대비)
        delete_targets = []      # 삭제 예정 이미지 (commit 후 실제 삭제)
            
        try:
            with self.db.begin(): # 자동 commit or rollback    
                
                # 게시글 조회
                board = self.db.query(Board).filter(
                    Board.board_no == board_no,
                    Board.board_del_fl == 'N'
                ).first()
                
                if not board:
                    raise NotFoundException("게시글을 찾을 수 없습니다.")
                
                # 작성자(권한) 확인
                if board.member_no != member_no:
                    raise ForbiddenException("게시글을 수정할 권한이 없습니다.")
                
                # 제목/내용 업데이트 (XSS 처리)
                board.board_title = Util.xss_handling(board_title)
                board.board_content = Util.xss_handling(board_content)
                board.b_update_date = datetime.now()
                
                # =============================
                # 이미지 삭제 처리 (DB만, 파일 X)
                # =============================
                if delete_image_orders:
                    delete_targets = self.db.query(BoardImg).filter(
                        BoardImg.board_no == board_no,
                        BoardImg.img_order.in_(delete_image_orders)
                    ).all()

                    for img in delete_targets:
                        self.db.delete(img)      
                        # 강제 DB update필요: 아래 current_count가 삭제되고 난 후의 남아있는 existing image 갯수 반영위해       
                        # with self.db.begin() 블록 종료에 의한 자동반영이전에 강제 반영하고 싶을때
                        self.db.flush() # 같은 Session()에서만
                
                # =============================
                # 새 이미지 추가
                # =============================
                if new_images:
                    # 현재 이미지 개수 확인
                    current_count = self.db.query(BoardImg).filter(
                        BoardImg.board_no == board_no
                    ).count()
                    
                    
                    if current_count + len(new_images) > self.max_images:
                        raise FileUploadException(
                            f"이미지는 최대 {self.max_images}개까지 가능합니다."
                        )
                    
                    # 새 이미지 순서 계산 (기존 이미지 다음부터)
                    max_order = current_count
                    
                    # 이미지 업로드 (순서 재조정)
                    for idx, image in enumerate(new_images):
                        board_img, saved_path = self._upload_single_image(
                            board_no, image, max_order + idx
                        )
                        uploaded_files.append(saved_path)       
                
                self.db.flush() # 같은 Session()에서만
                
                # 이미지 삭제 처리 후 img_order 재설정 (thumbnail 이미지 삭제경우 대비)
                # =============================
                # img_order 재정렬 (0부터 연속되게)
                # =============================
                # UPDATE나 commit()을 호출할 필요없음(b/c dirty checking)
                images = (
                    self.db.query(BoardImg)  # ORM객체 생성=> Session(self.db)에 attach된 상태 =>SQLAlchemy가 변경감지(dirty checking)을 자동수행
                    .filter(BoardImg.board_no == board_no)
                    .order_by(BoardImg.img_order.asc(), BoardImg.img_no.asc())
                    .all()
                ) # images: BoardImg객체들이 Session에 등록됨

                for new_order, img in enumerate(images):
                    img.img_order = new_order #
                
                # with self.db.begin() 블록 종료에 의한 자동반영이전에 강제 반영하고 싶을때
                self.db.flush() # 같은 Session()에서만
                self.db.commit()
                
            # =============================
            # commit 성공 이후
            # =============================

            # 삭제 이미지 실제 파일 삭제
            for img in delete_targets:
                file_path = Path(self.upload_dir) / img.img_path.lstrip("/")  / img.img_rename.lstrip("/") # file명 (현 Board_Img 테이블에서)
                if file_path.exists():
                    file_path.unlink()                
            
            self.db.refresh(board)
            
            return board
            
        except Exception as e:
            # rollback + 새로 업로드된 파일 제거
            self.db.rollback()

            for path in uploaded_files:
                if path.exists():
                    path.unlink()

            raise e    
    
    
    
    def _upload_single_image(self, board_no: int, image: UploadFile, order: int) ->  tuple[BoardImg, Path]:
        """단일 이미지 업로드,  tuple[BoardImg, Path]를 반환하도록만 살짝 수정"""
        original_filename = Util.sanitize_filename(image.filename)
        
        if not Util.validate_image_extension(original_filename, self.allowed_extensions):
            raise InvalidFileExtensionException(f"허용되지 않은 파일 형식입니다.")
        
        renamed_filename = Util.file_rename_uuid(original_filename)     
        save_dir = Path(self.upload_dir) / "images/board/freeboard"   # 현 oracle Board_Img 데이터베이스에 맞게  
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / renamed_filename # Path(self.upload_dir) / "images/board/freeboard" / renamed_filename
        
        try:
            with save_path.open("wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            board_img = BoardImg(
                img_path=f"/images/board/freeboard/", # 현 oracle Board_Img 데이터베이스에 맞게  
                img_orig=original_filename,
                img_rename=renamed_filename,
                img_order=order,
                board_no=board_no
            )
            
            self.db.add(board_img)
            return board_img, save_path 
            
        except Exception as e:
            if save_path.exists():
                save_path.unlink()
            raise FileUploadException(f"파일 업로드 실패: {str(e)}")
    
