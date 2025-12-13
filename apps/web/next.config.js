/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.nike.com",
      },
      {
        protocol: "https",
        hostname: "**.adidas.com",
      },
      {
        protocol: "https",
        hostname: "**.zalando.net",
      },
      {
        protocol: "https",
        hostname: "**.vinted.net",
      },
    ],
  },
};

module.exports = nextConfig;
