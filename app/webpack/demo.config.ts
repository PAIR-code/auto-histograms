/*
@license
Copyright 2019 Google LLC. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
  mode : 'development',
  devtool : 'inline-source-map',
  module : {
    rules :
    [
      {
        test : /\.ts$/,
        exclude : /node_modules/,
        use : 'ts-loader',
      },
      {
        test : /\.css$/i,
        loader : path.resolve(__dirname, './lit-css-loader.js'),
      },
    ]
  },
  devServer : {
    host : '0.0.0.0',
    port : 1234,
    disableHostCheck : true,
  },

  resolve : {
    modules : ['node_modules'],
    extensions : ['.ts', '.js'],
  },
  entry : './index.ts',
  output : {
    path : path.join(__dirname, '../build'),
    filename : 'bundle.min.js',
  },
  plugins :
  [
    new HtmlWebpackPlugin({
      template : path.join(__dirname, '../index.html'),
    }),
    new CopyWebpackPlugin([{from : 'static'}]),
    new MiniCssExtractPlugin({
      experimentalUseImportModule : true,
    }),
  ]
};
