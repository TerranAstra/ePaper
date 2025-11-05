
To see what’s failing and get back to 202, take these checks (all on the Pi):

1. **Make sure docker SQL Edge is up**  
   ```bash
   docker ps --format 'table {{.Names}}\t{{.Status}}'
   # expect frank-azure-sql-edge ... Up ...
   ```
   If it’s missing: `docker compose -f docker-compose.mssql.yml --profile pi up -d`.

2. **Verify the API is running with the right connection string**  
   The window where you ran `dotnet run` should be alive. Stop/restart with:
   ```bash
   export SQL_CONNECTION_STRING="Server=localhost,1433;User ID=sa;Password=Your_strong_password123;TrustServerCertificate=True;Encrypt=False;Database=FrankEvents;"
   dotnet run --project Frank.Events/Frank.Events.Api --urls http://0.0.0.0:5000
   ```
   After restart, hit the health checks in another terminal:
   ```bash
   curl -s http://localhost:5000/health
   # → {"ok":true,"service":"Frank.Events.Api"}

   curl -s http://localhost:5000/health/db
   # → {"ok":true}  (if it’s false you’ll get details in the JSON)
   ```

3. **Retry the sample POST with verbose output**  
   ```bash
   curl -v \
     -H "Content-Type: application/json" \
     -H "X-Source-Node-Id: pi01" \
     -d '{
       "EventId":"00000000-0000-0000-0000-000000000001",
       "SessionId":"sess-local-1",
       "AppId":"geminiStreaming",
       "Role":"system",
       "Text":"Pi test event",
       "IsFinal":true,
       "Timestamp":"'"$(date -Iseconds)"'",
       "Model":"gemini-2.5",
       "Voice":"Achird",
       "GroundingJson":null,
       "MetaJson":"{\"note\":\"smoke test\"}",
       "ProposedSavePath":"/data/audioStream/20251105/audioStream202511050653.TestEvent.sav",
       "SourceNodeId":"pi01"
     }' http://localhost:5000/events
   ```
   - The `-v` prints the HTTP response headers.  
   - If it still returns 500, the body now contains JSON like:  
     `{"error":"...","inner":"...","hint":"Verify SQL container ..."}`
   - At the same time, the API console window logs a stack trace; copy the `ERROR:` line if needed.

4. **If 500 persists: double-check SQL login**  
   - Try connecting with `tsql` to confirm the credentials:
     ```bash
     sudo apt install -y freetds-bin
     tsql -H 127.0.0.1 -p 1433 -U sa -P 'Your_strong_password123'
     ```
     If it refuses: either the password differs or the container isn’t listening.

5. **Once the POST returns 202**  
   - Keep the `curl` stanza from `CompletePiWalkthrough.md`, and optionally add a note in the doc: “If you get 500, rerun with `curl -v` and check `/health/db` or the API console for details.”

These steps give you visibility into why 500 happened and how to confirm the doc’s test works. If you still see 500 after these checks, grab the JSON error body and the console log and we can dig in further.