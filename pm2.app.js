module.exports = {
    apps: [{
        name: "ipv6_server",
        version: "0.0.1",
        script: "./go-proxy-ipv6-pool-auto/go-proxy-ipv6-pool/go-proxy-ipv6-pool",
        error_file: '/dev/null',
        out_file: '/dev/null',
    }
    ]
}
