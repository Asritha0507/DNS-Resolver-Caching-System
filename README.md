# DNS Resolver and Caching System

A Computer Networks project that implements a DNS resolver with TTL-based caching and analyzes the effect of caching on DNS response time and cache hit ratio.

## Features

- DNS resolution using A records
- UDP client-server communication
- TTL-based cache management
- Cache HIT and CACHE MISS detection
- Configurable maximum cache size
- Cache statistics and cache hit ratio
- TTL expiration handling
- DNS response-time measurement
- Flask-based web dashboard
- Live cache HIT/MISS response-time graph
- Performance experiments for cache size and response time

## System Architecture

```text
                 +----------------+
                 |     Client     |
                 +-------+--------+
                         |
                     UDP Query
                         |
                         v
              +---------------------+
              |    DNS Resolver     |
              +----------+----------+
                         |
                    Check Cache
                    /         \
                  HIT         MISS
                   |            |
                   |            v
                   |      +-------------+
                   |      | External DNS|
                   |      +------+------+
                   |             |
                   |         IP + TTL
                   |             |
                   |             v
                   |       Store in Cache
                   |             |
                   +------+------+
                          |
                          v
                    DNS Response