require 'date'
account = User.find_by!(username: 'root')
token = account.personal_access_tokens.create!(name: 'interview-automation', scopes: ['api', 'read_repository', 'write_repository'], expires_at: Date.today + 30)
token.set_token(ENV.fetch('BOOTSTRAP_TOKEN'))
token.save!
puts 'API token created'
