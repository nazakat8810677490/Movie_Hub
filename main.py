from fastapi import FastAPI, Request, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from bson import ObjectId
from fastapi import Form
from config.db import admins, customers, categories
from config.db import movies
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()
app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key= "CLOUDINARY_API_SECRET" 
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key= os.getenv("CLOUDINARY_API_KEY"),
    api_secret= os.getenv("CLOUDINARY_API_SECRET")
)

print("Cloud Name:", os.getenv("CLOUDINARY_CLOUD_NAME"))
print("API Key:", os.getenv("CLOUDINARY_API_KEY"))
print("API Secret:", os.getenv("CLOUDINARY_API_SECRET"))

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request= request,
        name= "index.html"
    )

@app.get("/create-admin")
def create_admin():
    admin = {
        "name": "admin",
        "email": "admin@gmail.com",
        "password": "1234",
        "role": "admin"
    }

    admins.insert_one(admin)
    return RedirectResponse(
        "/admin-login"
    )

@app.get("/admin-login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse(
        name= "admin/admin_login.html",
        request= request
    )

@app.post("/admin-login")
def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    admin = admins.find_one({
        "email": email,
        "password": password
    })

    request.session["role"] = admin["role"]

    if admin:
        return RedirectResponse(
            "/admin-dashboard",
            status_code= 302
        )
    return {"message": "Invalid email or password."}

@app.get("/admin-dashboard")
async def admin_dashboard(request: Request):

    role = request.session.get("role")

    if role != "admin":
        return RedirectResponse(
            "/admin-login",
            status_code=303
        )
    
    return templates.TemplateResponse(
        name= "admin/admin_dashboard.html",
        request= request
    )

# ---------------------add movie--------------------------------------

@app.get("/add-movie", response_class=HTMLResponse)
def add_movie_page(request: Request):
    category_data = categories.find()
    return templates.TemplateResponse(
        name = "movie/add_movie.html",
        request = request,
        context= {
            "categories": category_data
        }
    )

@app.post("/add-movie")
async def add_movie(
    title: str = Form(...),
    release_date: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    video: UploadFile = File(...)
):
    result = cloudinary.uploader.upload(
        video.file,
        resource_type = "video"
    )

    video_url = result["secure_url"]

    movies.insert_one({
        "title": title,
        "release_date": release_date,
        "description": description,
        "category": category,
        "video_url": video_url
    })
    return {"message": "movie added successfully"}


@app.get("/movies", response_class=HTMLResponse)
def movie_page(request: Request):
    movie_list = list(movies.find())
    role = request.session.get("role")
    return templates.TemplateResponse(
        name = "movie/movies.html",
        request = request,
        context={
            "movies": movie_list,
            "role": role
        }
    )

@app.get("/delete-movie/{_id}")
def delete_movie(_id: str):
    # movies.delete_one({
    #     "_id": ObjectId(_id)
    # })
    print("id :" , ObjectId(_id))

    return RedirectResponse(
        "/movies",
        status_code=302
    )

# --------------------------------Category----------------------------------------
@app.get("/add-category", response_class=HTMLResponse)
def add_category_page(request: Request):
    return templates.TemplateResponse(
        name = "category/add_category.html",
        request = request
    )

@app.post("/add-category")
def add_category(
    name: str = Form(...)
):
    category ={
        "name": name
    }

    categories.insert_one(category)
    response=  RedirectResponse(
        "/view-category",
        status_code=302
    )

    response.set_cookie(
        "message",
        "Category Added"
    )
    return response
    

# ------------------------------customer-------------------------------------

@app.get("/registration", response_class=HTMLResponse)
def registration_page(request: Request):
    return templates.TemplateResponse(
        name= "customer/registration.html",
        request= request
    )

@app.post("/registration")
def registration(
    name: str = Form(...),
    email: str = Form(...),
    ph_no: int = Form(...),
    password: str = Form(...)
):
    customer ={
        "name": name,
        "email": email,
        "ph_No": ph_no,
        "password": password,
        "role": "user"
    }
    custo = customers.find_one(customer)

    if custo:
       return {"message": "Customer Already Registered"}

    customers.insert_one(customer)
    return RedirectResponse(
        "/login",
        status_code= 302
    )

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        name= "customer/login.html",
        request= request
    )

@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    customer = customers.find_one({
        "email": email,
        "password": password
    })

    request.session["role"] = customer["role"]

    if customer:
        print(customer)
        return RedirectResponse(
            "/movies",
            status_code= 302
        )
    print(customer)
    return RedirectResponse(
        "/login",
        status_code= 302   
    )

@app.get("/dashboard",response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(
        name= "index.html",
        request= request
    )

# ---------------------------------------search-Bar-------------------------------------

@app.get("/search-movie") 
async def search_movie(
    request: Request,
    query: str = ""
) :

    movies_list = list(
        movies.find({
            "$or": [
                {
                    "title": {
                        "$regex": query,
                        "$options": "i"
                    }
                },
                {
                    "category": {
                        "$regex": query,
                        "$options": "i"
                    }
                },
                {
                    "description": {
                        "$regex": query,
                        "$options": "i"
                    }
                }
            ],

        })
    )

    return templates.TemplateResponse(
        name = "customer/search_result.html",
        request = request,
        context ={
            "movies": movies_list,
            "query": query
        }
    )