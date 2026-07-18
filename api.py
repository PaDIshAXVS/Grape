import os
import io
import shutil
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from core import Session, User, Grape, Image
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from PIL import Image as PILImage


app = FastAPI(title="Vineyard API")


UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")



class NewGrape(BaseModel):
    sort: str

class Image_description(BaseModel):
    text: str

class UpdateGrape(BaseModel):
    location: Optional[str] = None
    sort_text: Optional[str] = None
    date: Optional[datetime] = None
    briks: Optional[float] = None
    total: Optional[float] = None


#GET---------------------------------------------------------------------------------------------------------------------------------------------------------
@app.get('/')
async def root():
    return {'message': 'Добро пожаловать в API'}


@app.get('/user/{telegram_id}')
async def show_user_vineyard(request: Request, telegram_id: int):
    session = Session()

    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        session.close()
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    grapes_data = []
    for grape in user.vineyard:
        images_list = [{"id": img.id, "file_path": img.file_path, "description": img.description} for img in grape.images]
        
        grapes_data.append({
            'id': grape.id,
            'sort': grape.sort,
            'location': grape.location,
            'sort_text': grape.sort_text,
            'date': grape.date,
            'briks': grape.briks,
            'total': grape.total,
            'images': images_list
        })
    
    session.close()

    return templates.TemplateResponse(
        request=request,
        name='index.html',
        context={
            'telegram_id': telegram_id,
            'grapes_count': len(grapes_data),
            'vineyard': grapes_data
        }
    )


@app.get('/user/{telegram_id}/grape/{grape_id}')
async def show_user_grape(request: Request, telegram_id: int, grape_id: int):
    session = Session()

    grape = session.query(Grape).filter_by(id=grape_id).first()
    if not grape:
        session.close()
        raise HTTPException(status_code=404, detail='Grape not found')
    
    images_data = []
    for image in grape.images:
        images_data.append({
            'id': image.id,
            'file_path': image.file_path,
            'description': image.description
        })
    
    context = {
        'id': grape.id,
        'sort': grape.sort,
        'location': grape.location,
        'sort_text': grape.sort_text,
        'date': grape.date,
        'briks': grape.briks,
        'total': grape.total,
        'images': images_data,
        'telegram_id': telegram_id
    }

    session.close()

    return templates.TemplateResponse(
        request=request,
        name='grape.html',
        context=context
    )


@app.get('/user/{telegram_id}/grape/{grape_id}/image/{image_id}')
async def show_grape_image(request: Request, telegram_id: int, grape_id: int, image_id: int):
    session = Session()

    image = session.query(Image).filter_by(id=image_id).first()
    if not image:
        session.close()
        raise HTTPException(status_code=404, detail='Image not found')
    
    context = {
        'id': image.id,
        'file_path': image.file_path,
        'description': image.description,
        'grape_id': image.grape_id,
        'telegram_id': telegram_id
    }

    session.close()

    return templates.TemplateResponse(
        request=request,
        name='image.html',
        context=context
    )


#POST--------------------------------------------------------------------------------------------------------------------------------------------------------
@app.post('/user/{telegram_id}/add_grape')
async def add_grape(telegram_id: int, grape: NewGrape):
    session = Session()

    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        session.close()
        raise HTTPException(status_code=404, detail='User not found')
    
    db_grape = Grape(sort=grape.sort)
    user.add_grape(session, db_grape)

    session.close()

    return {'status': 'success'}


@app.post('/user/{telegram_id}/grape/{grape_id}/update')
async def update_grape(telegram_id: int, grape_id: int, data: UpdateGrape):
    session = Session()

    grape = session.query(Grape).filter_by(id=grape_id).first()
    if not grape:
        session.close()
        raise HTTPException(status_code=404, detail='Grape not found')
    
    if data.location is not None:
        grape.location = data.location
    if data.sort_text is not None:
        grape.sort_text = data.sort_text
    if data.date is not None:
        grape.date = data.date
    if data.briks is not None:
        grape.briks = data.briks
    if data.total is not None:
        grape.total = data.total

    session.commit()
    session.close()

    return {'status': 'success'}


@app.post('/user/{telegram_id}/grape/{grape_id}/image/{image_id}/description')
async def description(telegram_id: int, grape_id: int, image_id: int, data: Image_description):
    session = Session()

    image = session.query(Image).filter_by(id=image_id).first()
    if not image:
        session.close()
        raise HTTPException(status_code=404, detail='Image not found')
    
    image.description = data.text

    session.commit()
    session.close()

    return {'status': 'success'}


@app.post('/user/{telegram_id}/grape/{grape_id}/upload_image')
async def upload_image(telegram_id: int, grape_id: int, file: UploadFile = File(...)):
    session = Session()

    try:
        grape = session.query(Grape).filter_by(id=grape_id).first()
        if not grape:
            raise HTTPException(status_code=404, detail='Grape not found')

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        contents = await file.read()

        img = PILImage.open(io.BytesIO(contents))

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail((1600, 1600))

        unique_filename = f"{uuid4()}.jpg"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        img.save(file_path, "JPEG", quality=70, optimize=True)

        db_file_path = f"/static/uploads/{unique_filename}"

        db_image = Image(file_path=db_file_path, description=None)
        grape.add_image(session, db_image)

        return {'status': 'success', 'file_path': db_file_path}
    except Exception as e:
        print(f"[ERROR] Ошибка сжатия и сохранения фотографии: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сервера при сохранении файла: {str(e)}")
    finally:
        session.close()


#DELETE------------------------------------------------------------------------------------------------------------------------------------------------------
@app.delete('/user/{telegram_id}/grape/{grape_id}')
async def delete_grape(telegram_id: int, grape_id: int):
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        grape = session.query(Grape).filter_by(id=grape_id).first()

        if not user or not grape:
            raise HTTPException(status_code=404, detail='Not found')
        
        file_paths_to_delete = []
        for image in grape.images:
            local_path = image.file_path.lstrip('/')
            file_paths_to_delete.append(local_path)
        
        user.remove_grape(session, grape)
        
        for path in file_paths_to_delete:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"[INFO] Файл {path} успешно удален с сервера.")
                except Exception as file_err:
                    print(f"[WARNING] Не удалось физически удалить файл {path}: {file_err}")
                    
        return {'status': 'success'}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Ошибка при удалении куста винограда: {e}")
        raise HTTPException(status_code=500, detail="Ошибка на сервере при удалении куста")
    finally:
        session.close()