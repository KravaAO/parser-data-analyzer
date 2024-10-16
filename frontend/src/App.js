import './App.css';
import axios from 'axios';
import React from 'react';

class App extends React.Component {
  state = { details: [] }

  componentDidMount() {
    axios.get('http://127.0.0.1:8000/')
      .then(res => {
        const data = res.data;
        this.setState({
          details: data
        });
      })
      .catch(err => {
        console.log(err);
      })
  }

  render() {
    return (
      <div>
        <header>
          <h1>Youtube Data</h1>
        </header>
        <hr />
        <ul>
          {this.state.details.map((output, id) => (
            <li key={id}>
              <strong>Title:</strong> {output.title} <br />
              <strong>Channel:</strong> {output.channel}
            </li>
          ))}
        </ul>
      </div>
    );
  }
}

export default App;
