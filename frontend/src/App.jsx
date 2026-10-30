import { useEffect, useState } from 'react'

const VERDICTS = {
  PHISHING: { label: 'Looks like phishing', className: 'verdict danger' },
  SUSPICIOUS: { label: 'Suspicious', className: 'verdict caution' },
  LEGITIMATE: { label: 'Looks legitimate', className: 'verdict safe' },
}

const SCAN_STEPS = [
  ['Website link', 'A person enters the link they are unsure about.'],
  ['Feature extraction', 'The system reads 10 features of the link, such as its length, hyphens and use of HTTPS.'],
  ['XGBoost model', 'The model compares these features with patterns it learned in training.'],
  ['Known website check', 'The site is checked against 100,000 known websites, and for signs such as an imitated brand name or a short link.'],
  ['Result and reasons', 'The higher of the two scores is shown, with the reasons in plain words.'],
]

const BUILD_STEPS = [
  ['Public dataset', '11,055 website records from the UCI phishing websites dataset, with 30 features each.'],
  ['Split the data', '8,844 records for training and 2,211 held back for testing.'],
  ['Compare three models', 'Random Forest, Support Vector Machine and XGBoost, using all 30 features.'],
  ['Retrain for live use', 'XGBoost is retrained on the 10 features that can be read from a link alone.'],
  ['Store every scan', 'Spring Boot saves each result in PostgreSQL for the history and dashboard.'],
]

const RESULTS = [
  ['XGBoost, live scanner (10 features)', '90.68%', '91.79%', '86.73%', '89.19%', '6.17%', true],
  ['Random Forest (30 features)', '97.69%', '98.04%', '96.73%', '97.38%', '1.54%'],
  ['XGBoost (30 features)', '97.11%', '97.51%', '95.92%', '96.71%', '1.95%'],
  ['Support Vector Machine (30 features)', '94.98%', '95.88%', '92.65%', '94.24%', '3.17%'],
]

const STATUS = [
  ['Dataset and trained models', 'Complete'],
  ['Machine learning service with explanations (Python, Flask)', 'Complete'],
  ['Application server (Spring Boot)', 'Complete'],
  ['Scan history and dashboard (PostgreSQL)', 'Complete'],
  ['Website (React.js)', 'Complete'],
  ['Reading the contents of live web pages', 'Planned'],
]

const TEAM = [
  ['K. Swarupa Reddy', 'Team member'],
  ['K V M Shashank Reddy', 'Team member'],
  ['P. Sandeep', 'Team member'],
  ['N. Shiva Krishna', 'Project guide'],
]

function Flow({ steps }) {
  return (
    <ol className="flow">
      {steps.map(([title, text], index) => (
        <li key={title}>
          <em>Step {index + 1}</em>
          <b>{title}</b>
          <small>{text}</small>
        </li>
      ))}
    </ol>
  )
}

function Scanner({ onScanned }) {
  const [url, setUrl] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function scan(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })
      const body = await response.json()

      if (!response.ok) {
        setError(body.error || 'The scan failed. Try again.')
        return
      }

      setResult(body)
      onScanned()
    } catch {
      setError('The server is not responding. Check that it is running and try again.')
    } finally {
      setLoading(false)
    }
  }

  const verdict = result && VERDICTS[result.prediction]

  return (
    <>
      <form className="scan-form" onSubmit={scan}>
        <label htmlFor="url">Website link</label>
        <div className="scan-row">
          <input
            id="url"
            type="text"
            inputMode="url"
            autoComplete="off"
            spellCheck="false"
            placeholder="https://example.com"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
          />
          <button className="btn solid" type="submit" disabled={loading}>
            {loading ? 'Scanning' : 'Scan link'}
          </button>
        </div>
      </form>

      <div aria-live="polite">
        {error && <p className="error">{error}</p>}

        {result && (
          <div className="result">
            <p className={verdict.className}>{verdict.label}</p>
            <p className="result-url">{result.url}</p>
            <dl className="score-row">
              <div><dt>Threat score</dt><dd>{result.threatScore.toFixed(0)} / 100</dd></div>
              <div><dt>Threat level</dt><dd>{result.threatLevel}</dd></div>
              <div><dt>Model score</dt><dd>{result.modelScore.toFixed(0)}</dd></div>
              <div><dt>Rules score</dt><dd>{result.ruleScore.toFixed(0)}</dd></div>
            </dl>
            <h3>Why this result</h3>
            <ul className="reasons">
              {result.reasons.map((reason) => (
                <li key={reason.feature}>{reason.text}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <p className="note">This check reads the link only and does not open the website. Sites it cannot confirm are marked suspicious, and a clean result is not a guarantee of safety.</p>
    </>
  )
}

function Dashboard({ stats, history, failed }) {
  if (failed) {
    return <p className="error">The dashboard could not load. Check that the server is running.</p>
  }

  return (
    <>
      <dl className="stats">
        <div><dt>Total scans</dt><dd>{stats.total}</dd></div>
        <div><dt>Legitimate</dt><dd>{stats.legitimate}</dd></div>
        <div><dt>Suspicious</dt><dd>{stats.suspicious}</dd></div>
        <div><dt>Phishing</dt><dd>{stats.phishing}</dd></div>
      </dl>

      <h3>Recent scans</h3>
      {history.length === 0 ? (
        <p>No scans yet. Scan a link above and it will appear here.</p>
      ) : (
        <div className="table-scroll" tabIndex="0" role="region" aria-label="Recent scans">
          <table>
            <thead>
              <tr>
                <th scope="col">Link</th>
                <th scope="col">Result</th>
                <th scope="col" className="num">Score</th>
                <th scope="col">Scanned</th>
              </tr>
            </thead>
            <tbody>
              {history.map((scan) => (
                <tr key={scan.id}>
                  <th scope="row" className="link-cell">{scan.url}</th>
                  <td>{VERDICTS[scan.prediction].label}</td>
                  <td className="num">{scan.threatScore.toFixed(0)}</td>
                  <td>{new Date(scan.scannedAt).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

function App() {
  const [stats, setStats] = useState({ total: 0, legitimate: 0, suspicious: 0, phishing: 0 })
  const [history, setHistory] = useState([])
  const [failed, setFailed] = useState(false)

  async function refresh() {
    try {
      const [statsResponse, historyResponse] = await Promise.all([
        fetch('/api/stats'),
        fetch('/api/history'),
      ])

      if (!statsResponse.ok || !historyResponse.ok) throw new Error('Request failed')

      setStats(await statsResponse.json())
      setHistory(await historyResponse.json())
      setFailed(false)
    } catch {
      setFailed(true)
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh()
  }, [])

  return (
    <>
      <a className="skip" href="#main">Skip to main content</a>

      <div className="band">
        <div className="wrap">
          <span>Department of CSE</span>
          <span>Engineering Capstone Project, A.Y. 2026-2027</span>
        </div>
      </div>

      <header className="masthead">
        <div className="wrap">
          <a className="wordmark" href="#top">CyberShield AI</a>
          <nav aria-label="Main">
            <ul>
              <li><a href="#scan">Scan a link</a></li>
              <li><a href="#dashboard">Dashboard</a></li>
              <li><a href="#about">About</a></li>
              <li><a href="#how">How it works</a></li>
              <li><a href="#results">Results</a></li>
              <li><a href="#team">Team</a></li>
            </ul>
          </nav>
        </div>
      </header>

      <main id="main">
        <div className="intro" id="top">
          <div className="wrap">
            <div>
              <h1>Phishing detection using machine learning</h1>
              <p className="lead">CyberShield AI checks whether a website link looks legitimate or looks like phishing, and explains the reasons in plain language.</p>
              <div className="actions">
                <a className="btn solid" href="#scan">Scan a link</a>
                <a className="btn plain" href="#how">See how it works</a>
              </div>
            </div>
            <dl className="facts">
              <div><dt>Project type</dt><dd>Engineering capstone project</dd></div>
              <div><dt>Academic year</dt><dd>2026-2027</dd></div>
              <div><dt>Guide</dt><dd>N. Shiva Krishna</dd></div>
            </dl>
          </div>
        </div>

        <section className="block shade" id="scan">
          <div className="wrap">
            <h2>Scan a link</h2>
            <div className="body">
              <Scanner onScanned={refresh} />
            </div>
          </div>
        </section>

        <section className="block" id="dashboard">
          <div className="wrap">
            <h2>Dashboard</h2>
            <div className="body">
              <Dashboard stats={stats} history={history} failed={failed} />
            </div>
          </div>
        </section>

        <section className="block" id="about">
          <div className="wrap">
            <h2>About the project</h2>
            <div className="body">
              <p>CyberShield AI is a phishing detection and threat intelligence platform. It uses machine learning to study the features of a website link and classify it as legitimate, suspicious or phishing.</p>
              <p>Along with the result, it gives a threat score and shows the reasons, so a person can understand the warning as well as read it. Every scan is stored so that the history and dashboard stay up to date.</p>
            </div>
          </div>
        </section>

        <section className="block" id="problem">
          <div className="wrap">
            <h2>The problem</h2>
            <div className="body">
              <p>A phishing website copies a trusted site to trick people into giving away passwords or personal details. As more of daily life moves online, these attacks have become a major cybersecurity threat.</p>
              <p>Traditional methods rely on blacklists and fixed rules. They often miss new or carefully made phishing sites, because a site cannot be blocked until it is known. Machine learning can judge a link by its features, including links it has never seen before.</p>
            </div>
          </div>
        </section>

        <section className="block shade full" id="how">
          <div className="wrap">
            <h2>How it works</h2>
            <div className="body">
              <h3>Checking a link</h3>
              <Flow steps={SCAN_STEPS} />
              <h3>Building the system</h3>
              <Flow steps={BUILD_STEPS} />
            </div>
          </div>
        </section>

        <section className="block" id="results">
          <div className="wrap">
            <h2>Model results</h2>
            <div className="body">
              <p className="cap">Test results on 2,211 records held back from training</p>
              <div className="table-scroll" tabIndex="0" role="region" aria-label="Model results table">
                <table className="wide">
                  <thead>
                    <tr>
                      <th scope="col">Model</th>
                      <th scope="col" className="num">Accuracy</th>
                      <th scope="col" className="num">Precision</th>
                      <th scope="col" className="num">Recall</th>
                      <th scope="col" className="num">F1 score</th>
                      <th scope="col" className="num">False alarms</th>
                    </tr>
                  </thead>
                  <tbody>
                    {RESULTS.map(([model, accuracy, precision, recall, f1, alarms, top]) => (
                      <tr key={model} className={top ? 'top' : undefined}>
                        <th scope="row">{model}</th>
                        <td className="num">{accuracy}</td>
                        <td className="num">{precision}</td>
                        <td className="num">{recall}</td>
                        <td className="num">{f1}</td>
                        <td className="num">{alarms}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="note">False alarms are legitimate websites wrongly marked as phishing. The 30-feature models also use details from the web page itself, which the live scanner does not read, so its score is lower. These figures come from dataset records and do not include the warning sign rules.</p>

              <h3>Live scanner tested on real links</h3>
              <div className="table-scroll" tabIndex="0" role="region" aria-label="Real link test table">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Test set</th>
                      <th scope="col" className="num">Links</th>
                      <th scope="col" className="num">Flagged</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr><th scope="row">Phishing links not used while building the scanner</th><td className="num">3,000</td><td className="num">92.3%</td></tr>
                    <tr><th scope="row">Popular real websites on the known list</th><td className="num">3,000</td><td className="num">1.4%</td></tr>
                    <tr><th scope="row">Real websites not on the known list</th><td className="num">3,000</td><td className="num">98.3%</td></tr>
                  </tbody>
                </table>
              </div>
              <p className="note">Flagged means marked suspicious or phishing. Links came from the public Phishing.Database list and the Tranco list of popular websites. Only known websites are treated as safe, so a real site outside the list is flagged because it cannot be confirmed. Phishing placed on a known website can pass. It is a first check, not a complete defence.</p>
            </div>
          </div>
        </section>

        <section className="block shade" id="status">
          <div className="wrap">
            <h2>Project status</h2>
            <div className="body">
              <div className="table-scroll" tabIndex="0" role="region" aria-label="Project status table">
                <table>
                  <thead>
                    <tr><th scope="col">Part of the project</th><th scope="col">Status</th></tr>
                  </thead>
                  <tbody>
                    {STATUS.map(([part, state]) => (
                      <tr key={part}><th scope="row">{part}</th><td>{state}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        <section className="block" id="team">
          <div className="wrap">
            <h2>Project team</h2>
            <div className="body">
              <div className="table-scroll" tabIndex="0" role="region" aria-label="Project team table">
                <table>
                  <thead>
                    <tr><th scope="col">Name</th><th scope="col">Role</th></tr>
                  </thead>
                  <tbody>
                    {TEAM.map(([name, role]) => (
                      <tr key={name}><th scope="row">{name}</th><td>{role}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        <section className="block" id="contact">
          <div className="wrap">
            <h2>Contact</h2>
            <div className="body">
              <p>To see the project or ask about it, please speak to the team at the project expo, or contact the Department of CSE.</p>
            </div>
          </div>
        </section>
      </main>

      <footer>
        <div className="wrap">
          <span>CyberShield AI</span>
          <span>Department of CSE, Engineering Capstone Project, A.Y. 2026-2027</span>
        </div>
      </footer>
    </>
  )
}

export default App
