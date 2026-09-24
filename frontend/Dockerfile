# --- STAGE 1: Build ứng dụng React/Vite ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Nhận VITE_API_URL từ Render (Dashboard > Environment) truyền vào lúc build.
# Vite chỉ đọc được import.meta.env.VITE_* tại thời điểm build (npm run build),
# nên PHẢI khai báo ARG rồi gán sang ENV trước khi chạy build, nếu không biến
# trên Render Dashboard sẽ không có tác dụng gì với bản build ra.
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# --- STAGE 2: Dùng Nginx để phục vụ static files ---
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]