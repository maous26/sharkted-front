/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  generateBuildId: async () => {
    return `build-${Date.now()}`;
  },
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
      {
        protocol: "https",
        hostname: "**.courir.com",
      },
      {
        protocol: "https",
        hostname: "**.footlocker.fr",
      },
      {
        protocol: "https",
        hostname: "**.footlocker.com",
      },
      {
        protocol: "https",
        hostname: "images.footlocker.com",
      },
      {
        protocol: "https",
        hostname: "**.jdsports.fr",
      },
      {
        protocol: "https",
        hostname: "**.size.co.uk",
      },
      {
        protocol: "https",
        hostname: "i8.amplience.net",
      },
    ],
  },
};

module.exports = nextConfig;
