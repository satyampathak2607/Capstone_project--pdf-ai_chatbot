#!/bin/bash
cd backend
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app



