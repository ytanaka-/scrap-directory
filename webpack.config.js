const path = require('path')
const VueLoaderPlugin = require('vue-loader/lib/plugin')

module.exports = {
  mode: 'development',

  entry: path.join(__dirname, 'frontend/app.js'),

  output: {
    filename: 'bundle.js',
    path: path.join(__dirname, 'static/js')
  },

  module: {
    rules: [
      {
        test: /\.vue$/,
        loader: 'vue-loader'
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: 'babel-loader'
      },
      {
        test: /\.styl(us)?$/,
        use: [
          'vue-style-loader',
          'css-loader',
          'stylus-loader'
        ]
      },
      { 
        test: /.css$/,
        use: ['style-loader', 'css-loader']
      },
    ]
  },

  plugins: [
    new VueLoaderPlugin()
  ]
};