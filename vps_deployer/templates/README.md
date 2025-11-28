# Add this to your docker-stack.yml services:

  fastapi-app:
    image: my-registry/fastapi-app:latest # You need to build and push this image first!
    deploy:
      replicas: 1
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.fastapi.rule=PathPrefix(`/api/python`)"
        - "traefik.http.routers.fastapi.entrypoints=web"
        - "traefik.http.routers.fastapi.middlewares=auth" # Protected by same auth
        - "traefik.http.services.fastapi.loadbalancer.server.port=8000"

  bun-app:
    image: my-registry/bun-app:latest # You need to build and push this image first!
    deploy:
      replicas: 1
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.bun.rule=PathPrefix(`/api/bun`)"
        - "traefik.http.routers.bun.entrypoints=web"
        - "traefik.http.routers.bun.middlewares=auth" # Protected by same auth
        - "traefik.http.services.bun.loadbalancer.server.port=3000"
